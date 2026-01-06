import io

import qrcode


def generate_qr_bytes(text: str) -> bytes:
    img = qrcode.make(text)
    with io.BytesIO() as buffer:
        img.save(buffer)
        return buffer.getvalue()
