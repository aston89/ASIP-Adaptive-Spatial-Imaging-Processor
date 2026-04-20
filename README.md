# Adaptive Spatial Imaging Processor
**ASIP** is a stereo enhancement system based on local opportunity-driven additive processing.
Instead of applying global widening, static delays or fixed stereo field transformations, ASIP computes a time-frequency dependent spatial opportunity map that determines where and how small stereo differences can be introduced without disrupting the original mix structure.
The system operates in an additive-only regime, meaning it does not reconstruct, correct or rebalance the stereo image, it introduces a controlled secondary spatial layer derived from local signal properties.

## Core Principle
Traditional stereo imaging tools operate using explicit transformations such as:
- inter-channel delay (Haas-based widening)
- decorrelation filters
- mid/side gain scaling
- frequency-dependent panning

**ASIP instead follows a different assumption:**
Stereo width is not a parameter to apply globally but an emergent property of local perceptual tolerance in the signal structure.
From this, it computes a continuous opportunity field over time and frequency, representing where spatial separation can be introduced with minimal perceptual disruption.

## Processing Model
The processing pipeline can be summarized as:
- Mid/Side decomposition
- Spectral and temporal analysis of:
- coherence
- energy distribution
- phase dispersion
- transient density
- Construction of a local spatial opportunity map
- Generation of a micro-diffuse residual layer from the Side component
- Additive integration of this layer into the stereo field

**Importantly:**
The original Mid signal is never modified and the Side signal is not globally reshaped.

## Key Characteristics
ASIP does not subtract or compress the stereo field. All modifications are additive in nature.
Processing is driven by short-time spectral analysis, not global track statistics.
No thresholds or discrete mode switching are used. All transitions are smooth and sigmoid-based.
The amount and type of stereo enhancement depends on spectral density, inter-channel correlation, transient activity, local entropy of the Side field.

## Differences from Conventional Stereo Imagers

| Aspect           | Conventional Imagers         | ASIP                        |
| ---------------- | ---------------------------- | --------------------------- |
| Processing model | Global transformation        | Local opportunity field     |
| Stereo control   | Gain / width parameter       | Emergent spatial density    |
| Signal handling  | Modify existing stereo image | Add secondary spatial layer |
| Behavior         | Deterministic                | Content-dependent           |
| Transitions      | Mode/threshold-based         | Continuous                  |

## Use Cases

**Intended for:**
- subtle stereo enhancement on mixed material
- mastering-stage spatial refinement
- adding controlled width without altering tonal balance
- creative spatial modulation at higher settings

**Not intended as:**
- corrective stereo repair tool
- mixing automation replacement
- replacement for panning decisions

## Technical overview (Design philosophy)

The system is intentionally designed around the idea that:
```
Stereo space should be introduced, not rebalanced.
```

ASIP is built around a strictly additive stereo enhancement model that avoids global reconstruction of the input image.
Instead of enforcing a target stereo width or applying deterministic channel transformations, the system estimates local spatial opportunity across time-frequency space and applies only minimal, context-dependent augmentation to the side component.
The core assumption is that stereo information is not uniformly distributed, certain spectral regions and temporal events already contain sufficient spatial separation while others can tolerate subtle enhancement without altering the perceived mix balance.
ASIP therefore operates as a constrained perturbation system rather than a corrective imager.

The processing pipeline is based on four coupled principles:
- **Additive-only side synthesis**, no subtraction or destructive mid/side redistribution is performed on the original signal.
- **Local opportunity mapping**, a multi-factor estimation of spatial headroom derived from spectral density, inter-channel coherence and mid/side energy distribution.
- **Continuous psychoacoustic masking model**, weighting is governed by smooth statistical transitions (median/MAD-normalized sigmoid fields) rather than hard thresholds.
- **Entropy-aware spatial diffusion**, stereo widening is modulated by local spectral entropy, preventing over-processing in already complex or diffuse regions.

Transient regions and low-frequency content are explicitly protected using sigmoid functions (soft gating) rather than binary constraints ensuring that spatial enhancement does not interfere with punch or mono compatibility, all transformations are applied in the STFT domain and re-synthesized without global normalization, preserving the original energy profile.

## Why it does not behave like traditional stereo imagers
Most stereo imaging processors (including many “pro-grade” mastering tools) operate on a relatively shallow model: they apply fixed or semi-fixed mid/side gain manipulations, frequency-split widening or correlation-driven static corrections.
This often results in a globally imposed stereo shape that is independent of local musical context.
ASIP takes a fundamentally different approach, instead of treating stereo width as a parameter to be set, it treats it as an emergent property of local spectral and temporal structure, the process is driven by a continuously evaluated opportunity field rather than a direct transformation target.

**Key distinctions:**
- No global widening curve is applied. Width is not “set”, it is locally inferred.
- No frequency band is permanently “stretched” or “opened”. Any widening exists only where the signal structure allows it.
- Processing is strictly additive in the side domain, meaning the original stereo field is never collapsed or rebalanced to achieve an effect.
- Correlation is not used as a correction target but as one of several weak priors in a broader perceptual model.
- Temporal masking (transients) and spectral density are first-class constraints, not afterthoughts.
- Entropy in the side channel is used as a proxy for “already-complete spatial information”, reducing intervention where the mix is already self-sufficient.
- 
In contrast, many conventional imagers implicitly assume that “wider is better” within a bounded range, leading to uniform expansion artifacts, phase exaggeration or perceived haze when pushed beyond subtle settings.
ASIP avoids this by never attempting to reshape the stereo field globally, instead it introduces controlled micro-differences only where the signal structure suggests unused spatial capacity, the result is less a “widening effect” and more a **localized increase in spatial resolution**.

## Notes on Behavior
Due to its additive and content-dependent nature, ASIP may exhibit:
- subtle apparent motion in stereo field
- increased spatial depth perception without strong panning shifts
- non-linear response to dense or transient-rich material

These are emergent properties of the opportunity-based model rather than explicit modulation:
**--stereo (0.0 → 2.0+)** Controls the intensity of spatial layer generation.
- 0.0 = near-transparent operation (minimal spatial addition)
- 1.0 = balanced enhancement (recommended sweet spot)
- >1.0 = increasingly perceptible spatial movement and decorrelation behavior

**Even at 0.0, the system is not strictly bypassed but operates in a minimal additive regime.**

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

# Typical workflows

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

## Notes

ASIP does not perform global stereo reconstruction or panning correction.
All processing is additive and driven by local spectral and temporal features.
Behavior is continuous and content-dependent.
Output file will have same sample rate of source but with 32bit float depth.
Best used in conjunction before [CALP](https://github.com/aston89/CALP-Content-Aware-Loudness-Processor)














