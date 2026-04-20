#!/usr/bin/env python3

import argparse
import warnings
import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import gaussian_filter, gaussian_filter1d

warnings.filterwarnings("ignore")

EPS = 1e-8


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def weighted_mean(x, w):
    w_sum = np.sum(w) + EPS
    return np.sum(x * w) / w_sum


def weighted_mad(x, w, center=None):
    if center is None:
        center = weighted_mean(x, w)
    return weighted_mean(np.abs(x - center), w)


def normalize_01(x):
    x = np.asarray(x, dtype=np.float32)
    lo = np.min(x)
    hi = np.max(x)
    return (x - lo) / (hi - lo + EPS)


class ASIPAnalyzer:


    def __init__(self, audio, sr, verbose=False):
        self.audio = audio
        self.sr = sr
        self.verbose = verbose
        self.n_samples = audio.shape[1]
        self.duration = self.n_samples / sr

    def mid_side_decomposition(self):
        L, R = self.audio[0], self.audio[1]
        self.mid = (L + R) / 2.0
        self.side = (L - R) / 2.0
        return self.mid, self.side

    def compute_correlation_matrix(self, frame_length=2048, hop_length=512):
        L, R = self.audio[0], self.audio[1]
        n_frames = 1 + max(0, (len(L) - frame_length) // hop_length)

        correlations = np.zeros(n_frames, dtype=np.float32)
        window = signal.get_window("hann", frame_length)

        for i in range(n_frames):
            start = i * hop_length
            end = start + frame_length
            if end > len(L):
                break

            l_frame = L[start:end] * window
            r_frame = R[start:end] * window

            numerator = np.sum(l_frame * r_frame)
            denominator = np.sqrt(np.sum(l_frame ** 2) * np.sum(r_frame ** 2))
            correlations[i] = numerator / (denominator + EPS)

        return correlations

    def spectral_analysis(self):

        L, R = self.audio[0], self.audio[1]

        L_spec = librosa.stft(L, n_fft=2048, hop_length=512)
        R_spec = librosa.stft(R, n_fft=2048, hop_length=512)

        cross_spec = L_spec * np.conj(R_spec)

        Pxx = np.mean(np.abs(L_spec) ** 2, axis=1)
        Pyy = np.mean(np.abs(R_spec) ** 2, axis=1)
        Cxy = np.mean(cross_spec, axis=1)

        coherence = np.abs(Cxy) / (np.sqrt(Pxx * Pyy) + EPS)
        coherence = np.clip(coherence, 0.0, 1.0)

        phase_diff = np.angle(np.exp(1j * (np.angle(L_spec) - np.angle(R_spec))))
        phase_dispersion = np.std(phase_diff, axis=1)

        band_energy = 0.5 * (Pxx + Pyy)

        return L_spec, R_spec, coherence, band_energy, phase_dispersion

    def transient_detection(self):

        mid, side = self.mid, self.side

        onset_env_mid = librosa.onset.onset_strength(
            y=mid, sr=self.sr, hop_length=512
        )
        onset_env_side = librosa.onset.onset_strength(
            y=side, sr=self.sr, hop_length=512
        )

        return onset_env_mid, onset_env_side

    def pro_grade_profile(self):

        mid = self.mid
        side = self.side

        def profile(x):
            centroid = float(np.mean(librosa.feature.spectral_centroid(y=x, sr=self.sr)))
            bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=x, sr=self.sr)))
            flatness = float(np.mean(librosa.feature.spectral_flatness(y=x)))
            rms = float(np.sqrt(np.mean(x ** 2) + EPS))
            return {
                "centroid": centroid,
                "bandwidth": bandwidth,
                "flatness": flatness,
                "rms": rms,
            }

        mid_p = profile(mid)
        side_p = profile(side)
        width_index = side_p["rms"] / (mid_p["rms"] + EPS)

        transient_density = float(
            np.mean(librosa.onset.onset_strength(y=mid, sr=self.sr, hop_length=512))
        )

        return {
            "mid_profile": mid_p,
            "side_profile": side_p,
            "width_index": width_index,
            "transient_density": transient_density,
        }

    def analyze_all(self):
        self.mid_side_decomposition()
        corr = self.compute_correlation_matrix()
        L_spec, R_spec, band_corr, band_energy, phase_dispersion = self.spectral_analysis()
        onset_m, onset_s = self.transient_detection()
        loud_L, loud_R, loud_S = self.loudness_analysis_preliminary()
        pro_profile = self.pro_grade_profile()

        results = {
            "avg_correlation": float(np.mean(corr)) if len(corr) else 0.0,
            "min_correlation": float(np.min(corr)) if len(corr) else 0.0,
            "band_correlation": band_corr,
            "band_energy": band_energy,
            "phase_dispersion": phase_dispersion,
            "onset_env_mid": onset_m,
            "onset_env_side": onset_s,
            "loudness_side": loud_S,
            "loudness_LR_avg": (loud_L + loud_R) / 2.0,
            "L_spec": L_spec,
            "R_spec": R_spec,
            "pro_profile": pro_profile,
        }

        if self.verbose:
            print("[ANALYSIS]")
            print(f"  Avg Correlation:   {results['avg_correlation']:.3f}")
            print(f"  Min Correlation:   {results['min_correlation']:.3f}")
            print(f"  Side Loudness:     {results['loudness_side']:.2f} dB")
            print(f"  Width Index:       {pro_profile['width_index']:.3f}")
            print(f"  Mid Centroid:      {pro_profile['mid_profile']['centroid']:.1f} Hz")
            print(f"  Side Centroid:     {pro_profile['side_profile']['centroid']:.1f} Hz")
            print(f"  Mid Bandwidth:     {pro_profile['mid_profile']['bandwidth']:.1f} Hz")
            print(f"  Side Bandwidth:    {pro_profile['side_profile']['bandwidth']:.1f} Hz")
            print(f"  Mid Flatness:      {pro_profile['mid_profile']['flatness']:.3f}")
            print(f"  Side Flatness:     {pro_profile['side_profile']['flatness']:.3f}")
            print(f"  Transient Density: {pro_profile['transient_density']:.3f}")

        return results

    def loudness_analysis_preliminary(self):
        L, R = self.audio[0], self.audio[1]

        loudness_L = -0.691 + 10 * np.log10(np.mean(L ** 2) + EPS)
        loudness_R = -0.691 + 10 * np.log10(np.mean(R ** 2) + EPS)
        loudness_side = -0.691 + 10 * np.log10(np.mean(self.side ** 2) + EPS)

        return loudness_L, loudness_R, loudness_side


class LocalOpportunityStereoEnhancer:

    def __init__(self, sr, aggressive=False, verbose=False, stereo_factor=1.0):
        self.sr = sr
        self.aggressive = aggressive
        self.verbose = verbose
        self.n_fft = 2048
        self.hop_length = 512
        self.stereo_factor = stereo_factor

    def _build_transient_weight(self, onset_env_mid, onset_env_side, n_frames):

        onset = 0.82 * np.asarray(onset_env_mid, dtype=np.float32) + 0.18 * np.asarray(onset_env_side, dtype=np.float32)
        onset = gaussian_filter1d(onset, sigma=1.2, mode="nearest")

        if len(onset) < 4:
            return np.zeros(n_frames, dtype=np.float32)

        mu = np.median(onset)
        mad = 1.4826 * np.median(np.abs(onset - mu)) + EPS
        z = (onset - mu) / mad

        weight = sigmoid(z)
        weight = 0.05 + 0.95 * weight
        weight = gaussian_filter1d(weight, sigma=1.0, mode="nearest")

        if len(weight) != n_frames:
            x_old = np.linspace(0.0, 1.0, len(weight))
            x_new = np.linspace(0.0, 1.0, n_frames)
            weight = np.interp(x_new, x_old, weight)

        return np.clip(weight, 0.0, 1.0)

    def _complex_smooth(self, X):

        real = gaussian_filter(X.real, sigma=(0.8, 0.5), mode="nearest")
        imag = gaussian_filter(X.imag, sigma=(0.8, 0.5), mode="nearest")
        return real + 1j * imag

    def _entropy_map(self, S_spec):

        side_mag = np.abs(S_spec)
        col_sum = np.sum(side_mag, axis=0, keepdims=True) + EPS
        p = side_mag / col_sum

        entropy = -np.sum(p * np.log(p + EPS), axis=0) / np.log(p.shape[0] + EPS)
        entropy = gaussian_filter1d(entropy.astype(np.float32), sigma=1.0, mode="nearest")

        return np.clip(entropy, 0.0, 1.0)

    def _local_opportunity_map(self, L_spec, R_spec, analysis_results):

        M_spec = (L_spec + R_spec) / 2.0
        S_spec = (L_spec - R_spec) / 2.0

        M_mag = np.log1p(np.abs(M_spec))
        S_mag = np.log1p(np.abs(S_spec))

        coherence = np.abs(L_spec * np.conj(R_spec)) / (
            np.abs(L_spec) * np.abs(R_spec) + EPS
        )
        coherence = np.clip(coherence, 0.0, 1.0)

        # Smoothing space-temporal.
        mid_density = gaussian_filter(M_mag, sigma=(1.0, 1.0), mode="nearest")
        side_density = gaussian_filter(S_mag, sigma=(1.0, 1.0), mode="nearest")
        coh_smooth = gaussian_filter(coherence, sigma=(0.8, 0.8), mode="nearest")

        # Psychoacoustic-ish masking.
        md_mu = np.median(mid_density)
        md_mad = 1.4826 * np.median(np.abs(mid_density - md_mu)) + EPS
        masking = sigmoid((mid_density - md_mu) / md_mad)

        # Side Complexity convergence
        sd_mu = np.median(side_density)
        sd_mad = 1.4826 * np.median(np.abs(side_density - sd_mu)) + EPS
        side_room = 1.0 - sigmoid((side_density - sd_mu) / sd_mad)

        # local coherence above room, more space for micro widening.
        band_corr = np.asarray(analysis_results["band_correlation"], dtype=np.float32)
        coh_band_mu = weighted_mean(band_corr, np.maximum(analysis_results["band_energy"], EPS))
        coh_band_mad = weighted_mad(
            band_corr,
            np.maximum(analysis_results["band_energy"], EPS),
            center=coh_band_mu,
        )
        coh_band_spread = max(coh_band_mad, 0.04)

        coh_profile = band_corr[:, np.newaxis]
        coh_room = sigmoid((coh_smooth - coh_profile) / coh_band_spread)

        # Entropy: when side is rich, lesser influence.
        entropy_frame = self._entropy_map(S_spec)
        ent_mu = np.median(entropy_frame)
        ent_mad = 1.4826 * np.median(np.abs(entropy_frame - ent_mu)) + EPS
        entropy_room = 1.0 - sigmoid((entropy_frame - ent_mu) / ent_mad)
        entropy_room = entropy_room[np.newaxis, :]

        # Transient protection.
        transient_weight = self._build_transient_weight(
            analysis_results["onset_env_mid"],
            analysis_results["onset_env_side"],
            n_frames=M_spec.shape[1],
        )
        transient_room = 1.0 - 0.88 * transient_weight[np.newaxis, :]
        transient_room = np.clip(transient_room, 0.12, 1.0)

        # Phase dispersion and protection.
        phase_disp = np.asarray(analysis_results["phase_dispersion"], dtype=np.float32)
        phase_mu = np.median(phase_disp)
        phase_mad = 1.4826 * np.median(np.abs(phase_disp - phase_mu)) + EPS
        phase_room = sigmoid((phase_mu - phase_disp) / phase_mad)
        phase_room = phase_room[:, np.newaxis]

        # Gradual low-end protection.
        freqs = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)[:, np.newaxis]
        low_guard = sigmoid((freqs - 240.0) / 90.0)         # cresce gradualmente sopra i bassi
        air_guard = sigmoid((9000.0 - freqs) / 1800.0)      # evita di esagerare in aria estrema
        spectral_guard = 0.25 + 0.75 * low_guard * air_guard

        # Global budget very small, only additive.
        width_index = float(analysis_results["pro_profile"]["width_index"])
        material_drive = np.clip(analysis_results["avg_correlation"], 0.0, 1.0)

        # Already stereo enough -> budget almost none.
        global_budget = 0.010 + 0.040 * (1.0 - material_drive)
        global_budget *= 0.85 + 0.30 * (1.0 - np.clip(width_index, 0.0, 1.5))

        # knob global stereo.
        spatial_drive = self.stereo_factor

        # non lineare curve for musicality and more.
        spatial_drive = 0.35 + (spatial_drive ** 1.8) * 1.65

        global_budget *= spatial_drive

        opportunity = (
            masking
            * side_room
            * coh_room
            * entropy_room
            * transient_room
            * phase_room
            * spectral_guard
        )
		
		# safety coupling (more stereo = less aggression on transients and low-end).
        safety = 1.0 / (0.6 + 0.4 * self.stereo_factor)

        transient_room *= safety
        spectral_guard *= safety

        opportunity = gaussian_filter(opportunity, sigma=(0.8, 0.8), mode="nearest")

        # floor structure (NOT optional).
        opportunity = np.maximum(opportunity, 0.0015 * self.stereo_factor)

        opportunity = np.clip(opportunity, 0.02 * self.stereo_factor, 1.0)

        opportunity = global_budget * opportunity

        meta = {
            "global_budget": float(global_budget),
            "avg_opportunity": float(np.mean(opportunity)),
            "max_opportunity": float(np.max(opportunity)),
            "width_index": float(width_index),
            "material_drive": float(material_drive),
        }

        return opportunity, meta, S_spec

    def process(self, audio, analysis_results):

        L = audio[0].copy()
        R = audio[1].copy()

        L_spec = librosa.stft(L, n_fft=self.n_fft, hop_length=self.hop_length)
        R_spec = librosa.stft(R, n_fft=self.n_fft, hop_length=self.hop_length)

        M_spec = (L_spec + R_spec) / 2.0
        S_spec = (L_spec - R_spec) / 2.0

        opportunity, meta, S_spec = self._local_opportunity_map(
            L_spec, R_spec, analysis_results
        )

        # Residual micro-diffuser.
        S_smooth = self._complex_smooth(S_spec)
        micro_residual = (S_spec - S_smooth) * (1.2 + 0.3 * self.stereo_factor)

        # Additive layer is small and guided by opportunity map.
        add_layer = (micro_residual * opportunity) + (0.08 * S_spec * opportunity)
        add_layer *= (0.15 + 2.2 * self.stereo_factor)

        # Tiny side reinforcement where needed, additive.
        add_layer += (S_spec * (0.12 * opportunity))

        # soft Limit only on extra layer.
        ceiling = 0.10 if not self.aggressive else 0.14
        add_layer = np.tanh(add_layer / ceiling) * ceiling

        # Final add: original side + extra layer
        S_final = S_spec * (1.0 + 0.15 * self.stereo_factor) + add_layer

        L_new_spec = M_spec + S_final
        R_new_spec = M_spec - S_final

        L_out = librosa.istft(L_new_spec, hop_length=self.hop_length)
        R_out = librosa.istft(R_new_spec, hop_length=self.hop_length)

        min_len = min(len(L_out), len(R_out), len(L))
        L_out = L_out[:min_len]
        R_out = R_out[:min_len]

        if self.verbose:
            print("[LOCAL OPPORTUNITY MAP]")
            print(f"  Global budget:      {meta['global_budget']:.4f}")
            print(f"  Avg opportunity:    {meta['avg_opportunity']:.4f}")
            print(f"  Max opportunity:    {meta['max_opportunity']:.4f}")
            print(f"  Width index input:  {meta['width_index']:.3f}")
            print(f"  Material drive:     {meta['material_drive']:.3f}")

        return np.array([L_out, R_out])


class MetricsReporter:

    def __init__(self, original, processed, sr, verbose=False):
        self.original = original
        self.processed = processed
        self.sr = sr
        self.verbose = verbose

    def compute_metrics(self):
        L_orig, R_orig = self.original[0], self.original[1]
        L_proc, R_proc = self.processed[0], self.processed[1]

        min_len = min(len(L_orig), len(R_orig), len(L_proc), len(R_proc))
        L_orig = L_orig[:min_len]
        R_orig = R_orig[:min_len]
        L_proc = L_proc[:min_len]
        R_proc = R_proc[:min_len]

        corr_before = np.corrcoef(L_orig, R_orig)[0, 1]
        corr_after = np.corrcoef(L_proc, R_proc)[0, 1]

        side_before = L_orig - R_orig
        side_after = L_proc - R_proc

        side_energy_before = np.sqrt(np.mean(side_before ** 2))
        side_energy_after = np.sqrt(np.mean(side_after ** 2))

        mid_before = L_orig + R_orig
        mid_after = L_proc + R_proc

        mid_energy_before = np.sqrt(np.mean(mid_before ** 2))
        mid_energy_after = np.sqrt(np.mean(mid_after ** 2))

        width_before = side_energy_before / (mid_energy_before + EPS)
        width_after = side_energy_after / (mid_energy_after + EPS)

        mono_before = (L_orig + R_orig) * 0.5
        mono_after = (L_proc + R_proc) * 0.5
        mono_delta = np.sqrt(np.mean((mono_after - mono_before) ** 2))

        return {
            "correlation_before": corr_before,
            "correlation_after": corr_after,
            "side_energy_before": side_energy_before,
            "side_energy_after": side_energy_after,
            "side_gain_db": 20 * np.log10(side_energy_after / (side_energy_before + EPS)),
            "mid_energy_before": mid_energy_before,
            "mid_energy_after": mid_energy_after,
            "mid_preservation_db": 20 * np.log10(mid_energy_after / (mid_energy_before + EPS)),
            "width_before": width_before,
            "width_after": width_after,
            "mono_delta": mono_delta,
        }


def main():
    parser = argparse.ArgumentParser(
        description="ASIP v7 - Advanced Stereo Imaging Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""
              
    )

    parser.add_argument("input", help="Input WAV/MP3 file (stereo)")
    parser.add_argument("output", help="Output WAV file (32-bit float)")
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Slightly stronger widening budget",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed analysis",
    )
    parser.add_argument(
        "--stereo",
        type=float,
        default=1.0,
        help="Stereo imaging factor (0.0-2.0)"
    )

    args = parser.parse_args()

    print(f"[LOADING] {args.input}")
    audio, sr = librosa.load(args.input, sr=None, mono=False)

    if audio.ndim == 1:
        print("[ERROR] Input must be stereo!")
        return 1

    print(f"  Sample rate: {sr} Hz")
    print(f"  Duration: {audio.shape[1] / sr:.2f} s")
    print(f"  Channels: {audio.shape[0]}")

    print("\n[ANALYZING]")
    analyzer = ASIPAnalyzer(audio, sr, verbose=args.verbose)
    analysis_results = analyzer.analyze_all()

    print("\n[PROCESSING]")
    enhancer = LocalOpportunityStereoEnhancer(
        sr,
        aggressive=args.aggressive,
        verbose=args.verbose,
        stereo_factor=args.stereo,
    )
    processed = enhancer.process(audio, analysis_results)

    print("\n[METRICS]")
    reporter = MetricsReporter(audio, processed, sr, verbose=args.verbose)
    metrics = reporter.compute_metrics()

    print(f"  Correlation (before): {metrics['correlation_before']:.3f}")
    print(f"  Correlation (after):  {metrics['correlation_after']:.3f}")
    print(f"  Side energy gain:     {metrics['side_gain_db']:+.2f} dB")
    print(f"  Mid preservation:     {metrics['mid_preservation_db']:+.2f} dB")
    print(f"  Width index:          {metrics['width_before']:.3f} -> {metrics['width_after']:.3f}")
    print(f"  Mono delta RMS:       {metrics['mono_delta']:.6f}")

    print(f"\n[SAVING] {args.output}")
    sf.write(args.output, processed.T, sr, subtype="FLOAT")
    print("[DONE]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
