# import qrcode
# from PIL import Image
# import io
# import base64

# def create_qr_code(url: str, resolution: int) -> str:
#     # Génère le QR code brut
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=1
#     )
#     qr.add_data(url)
#     qr.make(fit=True)

#     img = qr.make_image(fill_color="black", back_color="white")

#     # Resize vers la résolution finale (ex: 32x32, 64x64)
#     img_resized = img.resize((resolution, resolution), Image.NEAREST)

#     # Convertir en base64 pour transport MQTT ou autre
#     buffered = io.BytesIO()
#     img_resized.save(buffered, format="PNG")
#     img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

#     return img_base64
####################################################################################

######################################### Créer Image QRCode en Base64 et ça FONCTIONNE ##################################################
# import qrcode
# from PIL import Image
# import io
# import base64

# def create_qr_code(url: str) -> Image.Image:
#     """Crée un QR code PIL.Image à partir d'une URL."""
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=1
#     )
#     qr.add_data(url)
#     qr.make(fit=True)

#     img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
#     return img


# def resize_qr_code(img: Image.Image, screen_count: int, matrix_count: int, shape: str) -> str:
#     """
#     Redimensionne l'image du QR code en fonction de la configuration écran/matrice
#     et retourne une image base64 encodée pour envoi.
#     """
#     # Détermine la taille de l'écran complet
#     if shape == "horizontal":
#         width = matrix_count * screen_count * 8
#         height = matrix_count * 8
#     elif shape == "vertical":
#         width = matrix_count * 8
#         height = matrix_count * screen_count * 8
#     else:  # "square" ou valeur par défaut
#         width = matrix_count * 8
#         height = matrix_count * 8

#     # Redimensionner l'image
#     resized_img = img.resize((width, height), Image.NEAREST)

#     # Encodage en base64
#     buffered = io.BytesIO()
#     resized_img.save(buffered, format="PNG")
#     img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

#     return img_base64
#################################### Fin du test qui fonctionne #####################################

import qrcode
from PIL import Image
import io
import base64
from typing import Tuple

# Générer un QR PIL.Image
# def create_qr_code(url: str) -> Image.Image:
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=1
#     )
#     qr.add_data(url)
#     qr.make(fit=True)
#     return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def create_qr_code(url: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,  # Force version 1
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Meilleure correction
        box_size=1,  # On va redimensionner après
        border=1
    )
    qr.add_data(url)
    # qr.make(fit=False)  # Pas d'auto-fit
    qr.make()
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

# Redimensionner pour produire une PIL.Image finale
def resize_qr_code(img: Image.Image,
                    screen_count: int,
                    matrix_count: int,
                    shape: str) -> Image.Image:
    # if shape == "horizontal":
    #     width = matrix_count * screen_count * 8
    #     height = matrix_count * 8
    # elif shape == "vertical":
    #     width = matrix_count * 8
    #     height = matrix_count * screen_count * 8
    # else:
    #     width = matrix_count * 8
    #     height = matrix_count * 8
    width = 48
    height = 48

    return img.resize((width, height), Image.NEAREST)

# Convertir PIL.Image RGB en base64 RAW RGB888
def qr_to_raw_base64(img: Image.Image) -> Tuple[int, int, str]:
    width, height = img.size
    pixels = list(img.getdata())
    raw = bytearray()
    for r, g, b in pixels:
        raw.extend((r, g, b))
    raw_b64 = base64.b64encode(raw).decode('ascii')
    return width, height, raw_b64