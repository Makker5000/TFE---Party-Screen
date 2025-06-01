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


def create_qr_code(url: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,  # Version 1 = 21x21, Version 2 = 25x25, ...
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Correction Minimale
        box_size=2,     # 2 pixels par module = 50x50 pour version 2
        border=0    # Pas de Bordure dans le QR Code
    )
    qr.add_data(url)
    # qr.make(fit=False)  # Pas d'auto-fit
    qr.make()

    # Générer l'image QR (21x21 pixels, noir et blanc)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return qr_image

# Redimensionner pour produire une PIL.Image finale
def resize_qr_code(img: Image.Image,
                    screen_count: int,
                    matrix_count: int,
                    shape: str) -> Image.Image:
    width = 48
    height = 48
    target_size = (width, height)

    # Créer une image 32x32 avec fond noir
    final_img = Image.new('RGB', target_size, color=(255, 255, 255))

    img_width, img_height = img.size

    # Calculer la position pour centrer le QR Code 21x21 dans le 32x32
    # (32-21)/2 = 5.5, donc on prend 5 pour avoir un léger décalage
    offset_x = (width - img_width) // 2  # 5 pixels
    offset_y = (height - img_height) // 2  # 5 pixels

    # Coller le QR Code au centre
    final_img.paste(img, (offset_x, offset_y))
    
    return final_img

# Convertir PIL.Image RGB en base64 RAW RGB888
def qr_to_raw_base64(img: Image.Image) -> Tuple[int, int, str]:
    width, height = img.size
    pixels = list(img.getdata())
    raw = bytearray()
    for r, g, b in pixels:
        raw.extend((r, g, b))
    raw_b64 = base64.b64encode(raw).decode('ascii')
    return width, height, raw_b64