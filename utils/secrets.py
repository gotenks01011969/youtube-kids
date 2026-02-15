from datetime import datetime

github_access_token = "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"
YOUTUBE_CLIENT_ID = "18489446057-5kngc92okd7a85g1nnuc3n2kpc2prn1p.apps.googleusercontent.com"
YOUTUBE_CLIENT_SECRET = "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"
YOUTUBE_REFRESH_TOKEN = "1//0g-QyJqpaFzfUCgYIARAAGBASNwF-L9IrFiBB6lC3LwsJbbPABTLP2Yjadpli_xRzyH-5ue4E5EACEdaGaODJ-VqF4UVTdG4XL5I"

heygen_keys = ["sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo",
               "sk_V2_hgu_k14QRkrT2E0_5AfrkltfRmtlinuEk8i6JmcdmzbzLFuo"]

groqcloud_keys = ["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",
               "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",
               "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",
               "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",
               "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",
               "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",
               "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"]

def get_current_day():
    # Get the current day of the week (0 = Monday, 6 = Sunday)
    current_day_index = datetime.today().weekday()  # Monday=0, Sunday=6
    current_day_index = (current_day_index + 1) % 7
    return current_day_index

def get_heygen_key():
    return heygen_keys[get_current_day()]

def get_groqcloud_key():
    return groqcloud_keys[get_current_day()]