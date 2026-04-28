from datetime import datetime

github_access_token = "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"
YOUTUBE_CLIENT_ID = "18489446057-5kngc92okd7a85g1nnuc3n2kpc2prn1p.apps.googleusercontent.com"
YOUTUBE_CLIENT_SECRET = "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"
YOUTUBE_REFRESH_TOKEN = "1//0g-QyJqpaFzfUCgYIARAAGBASNwF-L9IrFiBB6lC3LwsJbbPABTLP2Yjadpli_xRzyH-5ue4E5EACEdaGaODJ-VqF4UVTdG4XL5I"

heygen_keys = ["sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA",
               "sk_V2_hgu_k4Ihg5OYEP5_tniz0LrLlntbIF4nRUAPjpwdTYUdpxwA"]

# heygen_keys = ["sk_V2_hgu_kgG1cBpAA2w_NUD61AFzVSQI2vkPS0yofixUCZpfwJd5",
#                "sk_V2_hgu_kqn88Uaqv9T_c0z1vRKiLrvGRelkjMzccihUMaGBySxm",
#                "sk_V2_hgu_khf2lDmbZT3_FHZsd9f0zX8lyQKn39qtUYN1EiVhwu4g",
#                "sk_V2_hgu_k8JzKQSJwUf_QrWj74mYNeVgP32Xg8l6gy6UpLPyAVGS",
#                "sk_V2_hgu_kN70OgcrVHD_MIEPDcBdSGXICYfBWWX1cPJX4orhtsAR",
#                "sk_V2_hgu_kg5ZfeQOIO1_tgNeiVbj9zZAwOTneueKgfAsEcDB3w3W",
#                "sk_V2_hgu_kOOtmP2QVje_57Er7Lq5qAYPAkCxaTd4Orv48USrxVrc"]

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