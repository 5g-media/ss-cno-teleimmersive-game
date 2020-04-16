# =================================
#          VALID ACTIONS
# =================================
SET_VTRANS_PROCESSING_UNIT = 'set_vtranscoder_processing_unit'
SET_VTRANS_PROFILE = 'set_vtranscoder_profile'
SET_VTRANS_CLIENT_PROFILE = 'set_vtranscoder_client_profile'
NO_OP = 'no_operation'

# =================================
#   PSNR PER TRANSCODED PROFILE
# =================================
PSNR = {
    0: 33.02,
    1: 28.78,
    2: 28.02,
    3: 28.66,
    4: 30.00,
    5: 31.59,
}

# =================================
#         PROFILE ORIGINS
# =================================
GPU_PRODUCED_PROFILES = [3, 4, 5]
CPU_PRODUCED_PROFILES = [0, 1, 2]

# =================================
#          PROFILE TYPES
# =================================
VIDEO_PROFILES = [3, 4, 5]
JPEG_PROFILES = [0, 1, 2]

# =================================
#            VIM TAGS
# =================================
VTRANSCODER_3D = 'vtranscoder3d'
VTRANSCODER_3D_SPECTATORS = 'vtranscoder3d_spectators'
