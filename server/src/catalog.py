"""Kokoro v1.0 voice catalog."""

KOKORO_REPO_ID = 'hexgrad/Kokoro-82M'

SAMPLE_RATE = 24000

LANGUAGE_OPTIONS = {
    'a': 'American English',
    'b': 'British English', 
    'j': 'Japanese',
    'z': 'Mandarin Chinese',
    'f': 'French',
    'h': 'Hindi',
    'i': 'Italian',
    'e': 'Spanish',
    'p': 'Brazilian Portuguese'
}

ALL_VOICES = {
    'a': {
        'af_heart': 'F · Heart', 'af_alloy': 'F · Alloy', 'af_aoede': 'F · Aoede', 'af_bella': 'F · Bella',
        'af_jessica': 'F · Jessica', 'af_kore': 'F · Kore', 'af_nicole': 'F · Nicole', 'af_nova': 'F · Nova',
        'af_river': 'F · River', 'af_sarah': 'F · Sarah', 'af_sky': 'F · Sky',
        'am_adam': 'M · Adam', 'am_echo': 'M · Echo', 'am_eric': 'M · Eric', 'am_fenrir': 'M · Fenrir',
        'am_liam': 'M · Liam', 'am_michael': 'M · Michael', 'am_onyx': 'M · Onyx', 'am_puck': 'M · Puck',
        'am_santa': 'M · Santa'
    },
    'b': {
        'bf_alice': 'F · Alice', 'bf_emma': 'F · Emma', 'bf_isabella': 'F · Isabella', 'bf_lily': 'F · Lily',
        'bm_daniel': 'M · Daniel', 'bm_fable': 'M · Fable', 'bm_george': 'M · George', 'bm_lewis': 'M · Lewis'
    },
    'j': {
        'jf_alpha': 'F · Alpha', 'jf_gongitsune': 'F · Gongitsune', 'jf_nezumi': 'F · Nezumi',
        'jf_tebukuro': 'F · Tebukuro', 'jm_kumo': 'M · Kumo'
    },
    'z': {
        'zf_xiaobei': 'F · Xiaobei', 'zf_xiaoni': 'F · Xiaoni', 'zf_xiaoxiao': 'F · Xiaoxiao',
        'zf_xiaoyi': 'F · Xiaoyi', 'zm_yunjian': 'M · Yunjian', 'zm_yunxi': 'M · Yunxi',
        'zm_yunxia': 'M · Yunxia', 'zm_yunyang': 'M · Yunyang'
    },
    'f': {'ff_siwis': 'F · Siwis'},
    'h': {'hf_alpha': 'F · Alpha', 'hf_beta': 'F · Beta', 'hm_omega': 'M · Omega', 'hm_psi': 'M · Psi'},
    'i': {'if_sara': 'F · Sara', 'im_nicola': 'M · Nicola'},
    'e': {'ef_dora': 'F · Dora', 'em_alex': 'M · Alex', 'em_santa': 'M · Santa'},
    'p': {'pf_dora': 'F · Dora', 'pm_alex': 'M · Alex', 'pm_santa': 'M · Santa'}
}

FORMAT_OPTIONS = {'wav': 'WAV', 'flac': 'FLAC', 'ogg': 'OGG', 'mp3': 'MP3'}
