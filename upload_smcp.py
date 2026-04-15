"""一键上传 SMCP 知识文档到 LightRAG 知识库。
支持 .md 文本文件和 .pdf 文件（通过 /documents/upload 接口）。
"""
import json
import sys
import urllib.request
import pathlib
import mimetypes

BASE_URL = "http://localhost:9621"


def upload_text(content: str, description: str) -> dict:
    url = f"{BASE_URL}/documents/text"
    payload = json.dumps({"text": content, "description": description}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def upload_file(filepath: pathlib.Path) -> dict:
    """上传 PDF/DOCX 等二进制文件（multipart/form-data）。"""
    url = f"{BASE_URL}/documents/upload"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    mime, _ = mimetypes.guess_type(str(filepath))
    mime = mime or "application/octet-stream"

    body_parts = []
    body_parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{filepath.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
    )
    body_parts.append(filepath.read_bytes())
    body_parts.append(f'\r\n--{boundary}--\r\n'.encode())
    body = b"".join(body_parts)

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    base = pathlib.Path("F:/AI_CODING/JMU_nauticalEnglishOralAndListening")

    print("=== LightRAG SMCP 知识上传工具 ===\n")

    # 1️⃣ 上传 SMCP.md（文本接口）
    smcp_md = base / "SMCP_DATA" / "SMCP.md"
    if smcp_md.exists():
        print(f"[1/4] 正在上传 {smcp_md.name} ...")
        try:
            result = upload_text(
                smcp_md.read_text(encoding="utf-8"),
                "SMCP Standard Marine Communication Phrases - Full Standard Text (Markdown)"
            )
            print(f"      ✅ 成功: {result}\n")
        except Exception as e:
            print(f"      ❌ 失败: {e}\n")
    else:
        print(f"[1/4] ⚠️  文件不存在: {smcp_md}\n")

    # 2️⃣ 上传 smcp.pdf
    smcp_pdf = base / "SMCP_DATA" / "docs" / "smcp.pdf"
    if smcp_pdf.exists():
        print(f"[2/4] 正在上传 {smcp_pdf.name} ...")
        try:
            result = upload_file(smcp_pdf)
            print(f"      ✅ 成功: {result}\n")
        except Exception as e:
            print(f"      ❌ 失败: {e}\n")
    else:
        print(f"[2/4] ⚠️  文件不存在: {smcp_pdf}\n")

    # 3️⃣ 上传 A.918(22).pdf
    imo_pdf = base / "SMCP_DATA" / "docs" / "A.918(22).pdf"
    if imo_pdf.exists():
        print(f"[3/4] 正在上传 {imo_pdf.name} ...")
        try:
            result = upload_file(imo_pdf)
            print(f"      ✅ 成功: {result}\n")
        except Exception as e:
            print(f"      ❌ 失败: {e}\n")
    else:
        print(f"[3/4] ⚠️  文件不存在: {imo_pdf}\n")

    # 4️⃣ 上传 Maritime English PDF（第一个匹配）
    me_pdfs = list((base / "SMCP_DATA" / "docs").glob("*Maritime*English*.pdf"))
    if me_pdfs:
        me_pdf = me_pdfs[0]
        print(f"[4/4] 正在上传 {me_pdf.name} ...")
        try:
            result = upload_file(me_pdf)
            print(f"      ✅ 成功: {result}\n")
        except Exception as e:
            print(f"      ❌ 失败: {e}\n")
    else:
        print("[4/4] ⚠️  未找到 Maritime English PDF\n")

    print("=== 上传完成，请在 http://localhost:9621 查看处理进度 ===")


if __name__ == "__main__":
    main()
