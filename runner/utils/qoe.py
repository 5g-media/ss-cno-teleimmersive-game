import math

from runner.constants import PSNR


def compute_vq_itu(frame_rate, bit_rate):
    """Computes Video Quality according to the model suggested by the ITU for H.264 encoding.

    See more: https://www.itu.int/rec/T-REC-G.1070

    Parameters
    ----------
    frame_rate : float
        The frame rate as perceived by the spectator
    bit_rate : float
        The bit rate as perceived by the spectator

    Returns
    -------
    v_q : float
        The MOS measurement for reward

    """
    # Constant definitions for H.264 Codec, VGA Format and 9.2 Inches display
    coef = [0, 5.517, 0.0129, 3.459, 178.53, 1.02, 1.15, 0.000355, 0.114, 513.77, 0.736, -6.451, 13.684]

    # Video frame rate
    f_r_v = frame_rate
    # Video bit rate in kbps
    b_r_v = bit_rate * 1000
    # Packet loss rate
    p_pl_v = 0

    # Degree of video quality robustness due to frame rate
    d_fr_v = coef[6] + coef[7] * b_r_v
    # Degree of video quality robustness due to packet loss
    d_ppl_v = coef[10] + coef[11] * math.exp(-f_r_v / coef[8]) + coef[12] * math.exp(-b_r_v / coef[9])

    # Maximum video quality a each Bit Rate
    o_fr = coef[1] + coef[2] * b_r_v
    i_ofr = coef[3] - (coef[3] / (1 + (b_r_v / coef[4]) ** 5))
    # Basic video quality affected by the coding distortion
    i_coding = i_ofr * math.exp(-((math.log(f_r_v) - math.log(o_fr)) ** 2) / (2 * d_fr_v ** 2))
    # Video quality
    v_q = 1 + i_coding * math.exp(-p_pl_v / d_ppl_v)

    return v_q


def compute_qoe_psnr(frame_rate, profile):
    """Computes Mean Opinion Score through a PSNR based model.

    See more: https://ieeexplore.ieee.org/document/8463416

    Parameters
    ----------
    frame_rate : float
        The frame rate as this is perceived by the spectator
    profile : float
        The currently consumed profile of the spectator

    Returns
    -------
    mos : float
        The Mean Opinion Score (MOS) value

    """

    fr = 1.5 * frame_rate     # Model originally computed with 60 fps, we use 15 fps, compensate
    psnr = PSNR[profile]

    # Video Quality Contribution
    c = [0, -8.97, 0.056, 0.41, -0.0038, -0.001, 0.00079]
    video_quality = c[1] + (c[2] * fr) + (c[3] * fr) + (c[4] * (psnr**2)) + (c[5] * (fr**2)) + (c[6] * psnr * fr)

    # Re-activeness model contribution
    reactiveness = math.exp(0.84 + (4.43 / fr))

    # Positive Affect Model Contribution
    c = [0, 2.549, -0.055, -0.037, 0.00052, 0.0014, -0.00116]
    i_coding = c[1] + (c[2] * fr) + (c[3] * fr) + (c[4] * (psnr**2)) + (c[5] * (fr**2)) + (c[6] * psnr * fr)
    mos_zero = 4.2
    positive_affect = mos_zero - i_coding

    # MOS Final Computation
    mos = 1.102 + (0.59 * positive_affect) + (0.24 * reactiveness) + (0.25 * video_quality)
    return mos if mos <= 5 else 4.85
