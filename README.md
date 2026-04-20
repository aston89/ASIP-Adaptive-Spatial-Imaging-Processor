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

## IUse Cases

**Intended for:**
- subtle stereo enhancement on mixed material
- mastering-stage spatial refinement
- adding controlled width without altering tonal balance
- creative spatial modulation at higher settings

**Not intended as:**
- corrective stereo repair tool
- mixing automation replacement
- replacement for panning decisions

## Design Philosophy

The system is intentionally designed around the idea that:
'''
Stereo space should be introduced, not rebalanced.
'''
The goal is not to widen the signal but to create controlled spatial micro-variance that remains coherent with the original mix structure.

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














