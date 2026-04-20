# Adaptive Spatial Imaging Processor
ASIP is a stereo enhancement system based on **local opportunity-driven additive processing**.
Instead of applying global widening, static mid/side gains or fixed spatial transformations, ASIP computes a **time-frequency spatial opportunity field** that determines where minimal stereo perturbations can be introduced without altering the original mix structure.
The system operates in a strictly **additive-only regime**, it does not reconstruct, rebalance or correct the stereo image, it introduces a secondary spatial layer derived from local signal properties.

---

## Core Idea
Stereo width is not treated as a parameter, but as an **emergent property of local perceptual tolerance** in the signal.
ASIP models this by estimating where the stereo field has unused spatial capacity, based on:
- spectral energy distribution  
- inter-channel coherence  
- phase dispersion  
- transient density  
- local stereo entropy  

This produces a continuous **opportunity map** over time and frequency.

---

## Processing Model
1. Mid/Side decomposition  
2. Short-time spectral analysis (STFT domain)  
3. Estimation of spatial descriptors:
   - coherence
   - energy density
   - phase dispersion
   - transient activity
   - side entropy
4. Construction of a local opportunity field  
5. Generation of a micro-diffuse residual from the Side component  
6. Additive integration into the stereo field  

**Constraint:**  
The Mid signal remains untouched. The Side is not globally reshaped.

---

## Key Properties

- **Additive-only processing**: no destructive mid/side redistribution  
- **Local control model**: no global widening parameter  
- **Continuous behavior**: no thresholds or mode switching  
- **Sigmoid-based weighting**: smooth perceptual transitions  
- **Entropy-aware diffusion**: avoids over-processing dense stereo regions  
- **Transient protection**: temporal masking is explicitly modeled  
- **Gradual low-frequency constraint**: no hard gating  

---

## Differences from Conventional Stereo Imagers

| Aspect | Conventional Imagers | ASIP |
|--------|----------------------|------|
| Control model | Global width parameter | Local opportunity field |
| Processing | Mid/Side gain / delays | Additive side perturbation |
| Behavior | Deterministic | Signal-dependent |
| Frequency handling | Band-based widening | Continuous spectral weighting |
| Transient handling | Optional / external | Integrated constraint |
| Goal | Stereo expansion | Spatial information emergence |

Unlike traditional tools that assume “wider is better”, ASIP does not enforce stereo expansion, it only introduces spatial variation where the signal structure allows it.

---

## Behavior
ASIP produces emergent spatial effects such as:
- increased perceived depth without global widening
- localized stereo motion
- micro-diffuse widening in sparse regions
- stable mono compatibility under subtle settings

These effects are not explicitly modulated, but arise from the opportunity-driven model.

---

## Stereo Control
```
--stereo <float>
```
Controls the intensity of spatial layer generation:
- `0.0` → minimal additive perturbation (near-transparent regime)
- `1.0` → balanced enhancement (recommended)
- `>1.0` → pronounced spatial activity / creative behavior

Even at `0.0`, the system remains active in a minimal additive regime rather than being fully bypassed.

---

## Intended Use

**Suitable for:**
- mastering-stage spatial refinement  
- subtle stereo enhancement on mixed material  
- controlled widening without tonal alteration  
- creative spatial processing at higher intensities  

**Not intended for:**
- stereo correction or repair  
- mixing automation replacement  
- panning substitution  

---

## Design Principle
> **Stereo space is not enforced. It is inferred.**
ASIP treats stereo imaging as a constrained perturbation problem rather than a transformation target.
The output is a secondary spatial layer shaped by local perceptual tolerance rather than global manipulation of the stereo field.

---

## Notes
All processing is performed in the STFT domain and reconstructed without global normalization.  
Output is 32-bit floating point WAV, preserving original energy structure.
Best used as a pre-master spatial refinement stage or creative stereo processor.
Best used in conjunction before [CALP](https://github.com/aston89/CALP-Content-Aware-Loudness-Processor)

---

# Usage parameters

### Basic
``` bash
python ASIP_DSP.py input.wav output.wav
```
Default mode applies a balanced additive stereo enhancement based on local opportunity mapping.

### Stereo intensity
``` bash
--stereo <float>
```
Controls the strength of spatial layer generation.
-   `0.0` → near-transparent processing (minimal spatial addition)
-   `1.0` → balanced enhancement (recommended)
-   `>1.0` → creative / pronounced spatial movement

Example:
``` bash
python ASIP_DSP.py input.wav output.wav --stereo 1.0
```

### Aggressive mode
``` bash
--aggressive
```
Increases the upper bound of the additive layer. Intended for creative or sound design use.

Example:
``` bash
python ASIP_DSP.py input.wav output.wav --stereo 1.5 --aggressive
```

### Verbose mode
``` bash
--verbose
```
Prints analysis metrics including correlation, width index, and spectral descriptors.

Example:
``` bash
python ASIP_DSP.py input.wav output.wav --verbose
```

### Typical workflows

### Mastering enhancement (subtle)
``` bash
python ASIP_DSP.py mix.wav master.wav --stereo 0.3
```

### Standard enhancement
``` bash
python ASIP_DSP.py mix.wav master.wav --stereo 1.0
```

### Creative widening / spatial motion
``` bash
python ASIP_DSP.py mix.wav fx.wav --stereo 1.8 --aggressive
```




