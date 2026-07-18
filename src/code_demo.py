"""Mô phỏng cập nhật firmware IoT an toàn trong môi trường cục bộ.

Luồng bảo vệ gồm: manifest được ký RSA-PSS, SHA-256, mã hóa AES-256-GCM,
bọc khóa AES bằng RSA-OAEP, chống rollback bằng sequence và rollback khi
self-test thất bại. Tất cả khóa riêng chỉ tồn tại trong thư mục tạm khi chạy.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import logging
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


MAGIC = b"SFWU1"
HEADER_LIMIT = 64 * 1024
FIRMWARE_LIMIT = 4 * 1024 * 1024
TARGET = "iot-demo-board-v1"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
LOG_DIR = RESULTS_DIR / "logs"
PACKAGE_DIR = RESULTS_DIR / "packages"
DEVICE_DIR = RESULTS_DIR / "device_state"


class UpdateRejected(RuntimeError):
    """Bản cập nhật bị từ chối do không thỏa chính sách an toàn."""


@dataclass(frozen=True)
class KeyMaterial:
    vendor_private: rsa.RSAPrivateKey
    vendor_public: rsa.RSAPublicKey
    device_private: rsa.RSAPrivateKey
    device_public: rsa.RSAPublicKey


def canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_keys() -> KeyMaterial:
    vendor_private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    device_private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    return KeyMaterial(
        vendor_private=vendor_private,
        vendor_public=vendor_private.public_key(),
        device_private=device_private,
        device_public=device_private.public_key(),
    )


def export_public_key(key: rsa.RSAPublicKey, path: Path) -> None:
    path.write_bytes(
        key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def build_manifest(firmware: bytes, version: str, sequence: int) -> dict[str, Any]:
    return {
        "schema": "secure-firmware-manifest/v1",
        "target": TARGET,
        "version": version,
        "sequence": sequence,
        "size": len(firmware),
        "sha256": sha256_hex(firmware),
        "signature_algorithm": "RSA-PSS-SHA256",
        "encryption_algorithm": "AES-256-GCM",
        "key_wrap_algorithm": "RSA-OAEP-SHA256",
    }


def sign_manifest(
    manifest: dict[str, Any], private_key: rsa.RSAPrivateKey
) -> str:
    signature = private_key.sign(
        canonical_json(manifest),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("ascii")


def verify_manifest_signature(
    manifest: dict[str, Any], signature_b64: str, public_key: rsa.RSAPublicKey
) -> None:
    try:
        public_key.verify(
            base64.b64decode(signature_b64, validate=True),
            canonical_json(manifest),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError) as exc:
        raise UpdateRejected("Chữ ký manifest không hợp lệ") from exc


def create_package(
    firmware_path: Path,
    output_path: Path,
    version: str,
    sequence: int,
    keys: KeyMaterial,
) -> dict[str, Any]:
    firmware = firmware_path.read_bytes()
    if not firmware or len(firmware) > FIRMWARE_LIMIT:
        raise ValueError("Kích thước firmware ngoài giới hạn demo")

    manifest = build_manifest(firmware, version, sequence)
    signature = sign_manifest(manifest, keys.vendor_private)
    aad = canonical_json({"manifest": manifest, "signature": signature})
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext_and_tag = AESGCM(aes_key).encrypt(nonce, firmware, aad)
    wrapped_key = keys.device_public.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    header = {
        "manifest": manifest,
        "signature": signature,
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
    }
    header_bytes = canonical_json(header)
    if len(header_bytes) > HEADER_LIMIT:
        raise ValueError("Header vượt giới hạn")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes + ciphertext_and_tag
    )
    return manifest


def parse_package(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    if len(raw) < len(MAGIC) + 4 or raw[: len(MAGIC)] != MAGIC:
        raise UpdateRejected("Magic/version gói cập nhật không hợp lệ")
    header_length = struct.unpack(">I", raw[len(MAGIC) : len(MAGIC) + 4])[0]
    if header_length <= 0 or header_length > HEADER_LIMIT:
        raise UpdateRejected("Độ dài header không hợp lệ")
    header_start = len(MAGIC) + 4
    payload_start = header_start + header_length
    if payload_start >= len(raw):
        raise UpdateRejected("Gói cập nhật bị cắt ngắn")
    try:
        header = json.loads(raw[header_start:payload_start].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateRejected("Header JSON không hợp lệ") from exc
    return header, raw[payload_start:]


def load_state() -> dict[str, Any]:
    state_path = DEVICE_DIR / "state.json"
    if not state_path.exists():
        return {"version": "1.0.0", "sequence": 1}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    DEVICE_DIR.mkdir(parents=True, exist_ok=True)
    (DEVICE_DIR / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def apply_update(
    package_path: Path,
    vendor_public: rsa.RSAPublicKey,
    device_private: rsa.RSAPrivateKey,
) -> str:
    header, ciphertext_and_tag = parse_package(package_path)
    try:
        manifest = header["manifest"]
        signature = header["signature"]
        nonce = base64.b64decode(header["nonce"], validate=True)
        wrapped_key = base64.b64decode(header["wrapped_key"], validate=True)
    except (KeyError, TypeError, ValueError) as exc:
        raise UpdateRejected("Thiếu trường bắt buộc trong header") from exc

    verify_manifest_signature(manifest, signature, vendor_public)
    if manifest.get("target") != TARGET:
        raise UpdateRejected("Firmware không dành cho thiết bị này")
    if not isinstance(manifest.get("sequence"), int):
        raise UpdateRejected("Sequence không hợp lệ")

    state = load_state()
    if manifest["sequence"] <= int(state["sequence"]):
        raise UpdateRejected(
            f"Chống rollback: sequence {manifest['sequence']} <= {state['sequence']}"
        )

    try:
        aes_key = device_private.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        aad = canonical_json({"manifest": manifest, "signature": signature})
        firmware = AESGCM(aes_key).decrypt(nonce, ciphertext_and_tag, aad)
    except Exception as exc:
        raise UpdateRejected("Giải mã/xác thực AES-GCM thất bại") from exc

    if len(firmware) != manifest.get("size"):
        raise UpdateRejected("Kích thước firmware không khớp manifest")
    if sha256_hex(firmware) != manifest.get("sha256"):
        raise UpdateRejected("SHA-256 firmware không khớp manifest")

    DEVICE_DIR.mkdir(parents=True, exist_ok=True)
    active = DEVICE_DIR / "active_firmware.bin"
    staged = DEVICE_DIR / "staged_firmware.bin"
    backup = DEVICE_DIR / "backup_firmware.bin"
    staged.write_bytes(firmware)
    if active.exists():
        shutil.copy2(active, backup)

    if b"SELF_TEST=PASS" not in firmware:
        staged.unlink(missing_ok=True)
        if backup.exists():
            shutil.copy2(backup, active)
        raise UpdateRejected("Self-test thất bại; đã rollback về firmware trước")

    os.replace(staged, active)
    save_state({"version": manifest["version"], "sequence": manifest["sequence"]})
    return f"Đã cài phiên bản {manifest['version']} (sequence {manifest['sequence']})"


def tamper_package(source: Path, destination: Path) -> None:
    raw = bytearray(source.read_bytes())
    raw[-1] ^= 0x01
    destination.write_bytes(raw)


def tamper_manifest_signature(source: Path, destination: Path) -> None:
    """Tạo gói có chữ ký manifest sai nhưng vẫn giữ cấu trúc gói hợp lệ."""
    raw = source.read_bytes()
    header_length = struct.unpack(">I", raw[len(MAGIC) : len(MAGIC) + 4])[0]
    header_start = len(MAGIC) + 4
    payload_start = header_start + header_length
    header = json.loads(raw[header_start:payload_start].decode("utf-8"))
    signature = header["signature"]
    header["signature"] = ("A" if signature[0] != "A" else "B") + signature[1:]
    header_bytes = canonical_json(header)
    if len(header_bytes) != header_length:
        raise ValueError("Không thể giữ nguyên độ dài header khi sửa chữ ký")
    destination.write_bytes(
        MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes + raw[payload_start:]
    )


def run_case(name: str, action: Any, expected: str) -> dict[str, str]:
    try:
        message = action()
        actual = "ACCEPT"
    except UpdateRejected as exc:
        message = str(exc)
        actual = "REJECT"
    passed = actual == expected
    logging.info("CASE=%s EXPECTED=%s ACTUAL=%s RESULT=%s DETAIL=%s", name, expected, actual, "PASS" if passed else "FAIL", message)
    return {
        "case": name,
        "expected": expected,
        "actual": actual,
        "result": "PASS" if passed else "FAIL",
        "detail": message,
    }


def configure_logging() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "secure_update_demo.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_path, mode="w", encoding="utf-8"), logging.StreamHandler()],
    )
    return log_path


def reset_demo_state() -> None:
    if DEVICE_DIR.exists():
        shutil.rmtree(DEVICE_DIR)
    DEVICE_DIR.mkdir(parents=True)
    shutil.copy2(DATA_DIR / "firmware_v1.bin", DEVICE_DIR / "active_firmware.bin")
    save_state({"version": "1.0.0", "sequence": 1})


def run_demo() -> int:
    log_path = configure_logging()
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    reset_demo_state()
    keys = generate_keys()
    export_public_key(keys.vendor_public, RESULTS_DIR / "demo_vendor_public.pem")

    manifest_v2 = create_package(DATA_DIR / "firmware_v2.bin", PACKAGE_DIR / "firmware_v2.sfwu", "2.0.0", 2, keys)
    create_package(DATA_DIR / "firmware_v1.bin", PACKAGE_DIR / "firmware_v1_rollback.sfwu", "1.0.0", 1, keys)
    create_package(DATA_DIR / "firmware_v3_bad.bin", PACKAGE_DIR / "firmware_v3_bad.sfwu", "3.0.0", 3, keys)
    (RESULTS_DIR / "manifest_v2.json").write_text(
        json.dumps(manifest_v2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    signed_header_v2, _ = parse_package(PACKAGE_DIR / "firmware_v2.sfwu")
    (RESULTS_DIR / "signed_manifest_v2.json").write_text(
        json.dumps(
            {
                "manifest": signed_header_v2["manifest"],
                "signature": signed_header_v2["signature"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    tamper_package(PACKAGE_DIR / "firmware_v2.sfwu", PACKAGE_DIR / "firmware_v2_tampered.sfwu")
    tamper_manifest_signature(
        PACKAGE_DIR / "firmware_v2.sfwu",
        PACKAGE_DIR / "firmware_v2_bad_signature.sfwu",
    )

    def apply_from_clean_state(package: Path) -> str:
        reset_demo_state()
        return apply_update(package, keys.vendor_public, keys.device_private)

    rows = [
        run_case("valid_signed_update", lambda: apply_from_clean_state(PACKAGE_DIR / "firmware_v2.sfwu"), "ACCEPT"),
        run_case("tampered_manifest_signature", lambda: apply_from_clean_state(PACKAGE_DIR / "firmware_v2_bad_signature.sfwu"), "REJECT"),
        run_case("tampered_ciphertext", lambda: apply_from_clean_state(PACKAGE_DIR / "firmware_v2_tampered.sfwu"), "REJECT"),
        run_case("rollback_sequence", lambda: apply_from_clean_state(PACKAGE_DIR / "firmware_v1_rollback.sfwu"), "REJECT"),
        run_case("failed_self_test", lambda: apply_from_clean_state(PACKAGE_DIR / "firmware_v3_bad.sfwu"), "REJECT"),
    ]
    matrix_path = RESULTS_DIR / "test_matrix.csv"
    with matrix_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["result"] != "PASS"]
    logging.info("SUMMARY total=%d pass=%d fail=%d", len(rows), len(rows) - len(failures), len(failures))
    logging.info("OUTPUT log=%s matrix=%s", log_path, matrix_path)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Chạy toàn bộ ma trận kiểm thử cục bộ")
    args = parser.parse_args()
    if not args.demo:
        parser.print_help()
        return 0
    with tempfile.TemporaryDirectory(prefix="secure-fw-demo-"):
        return run_demo()


if __name__ == "__main__":
    raise SystemExit(main())
