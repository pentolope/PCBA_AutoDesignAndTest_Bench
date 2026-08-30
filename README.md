# PCBA AutoDesignAndTest — 32-board benchmark

Thirty-two intentionally heterogeneous PCBA design problems, one Git repository
each, catalogued here. The suite exists to measure automated PCBA design across
a range that a single board cannot cover: two-layer digital, sensors, precision
analog, industrial I/O, motor and power electronics, RF, high-speed digital,
FPGA and DDR3, constrained mechanical geometry, and a sixteen-channel circular
PDM microphone array.

Every board repository is a consumer of one shared toolkit,
[`PCBA_AutoDesignAndTest`](https://github.com/pentolope/PCBA_AutoDesignAndTest), and owns nothing
generic. The toolkit owns no board. That boundary is what makes thirty-two
results comparable.

## The graph

A recursive clone produces four levels:

```
PCBA_AutoDesignAndTest_Bench
└── boards/NN_PCBA_*                      32 board repositories
    ├── BRIEF.md                          the supplied brief, authoritative
    ├── board/requirements.json           what the brief fixes vs. leaves open
    └── tooling/PCBA_AutoDesignAndTest    the shared toolkit, pinned
        └── tooling/KiCadRoutingTools     the router, pinned on pcba-autonomy
```

All thirty-two boards resolve the **same** toolkit commit and the **same**
router commit. A benchmark whose boards run different toolkits is not one
benchmark, and `scripts/check_graph.py` fails if they diverge.

## Getting it

```bash
git clone --recursive https://github.com/pentolope/PCBA_AutoDesignAndTest_Bench.git
```

If you already have a shallow or non-recursive clone:

```bash
git submodule update --init --recursive
```

**That clone is about 3.2 GB and took 6.5 minutes when this repository was
established** — every one of the thirty-two boards carries its own checkout of
the toolkit and of the router, so the router's ~42 MB is paid thirty-two times.
That is the price of each board resolving a pinned toolkit independently, and it
is what makes a result attributable to a commit.

To read the briefs and the catalogue without any of that, clone without
`--recursive` and take the boards one level deep:

```bash
git clone https://github.com/pentolope/PCBA_AutoDesignAndTest_Bench.git
```

```bash
git submodule update --init
```

That is **about 12 MB** — all thirty-two briefs, requirement splits and
architecture worksheets, and no toolkit copies. Enough to read the suite; not
enough to run it. Add `--recursive` to the second command when you need to run
anything.

Then prove the graph is what it claims to be:

```bash
python3 scripts/check_graph.py
```

It checks all four levels — declared, recorded, checked out and identifiable —
that every board resolves one shared toolkit and router commit, that each
board's catalogue entry agrees with `boards_index.json`, and that the brief
digest each board recorded still describes its brief's bytes.

Straight after a non-recursive clone, before any submodule is populated, use
`--shallow`: it proves every declaration and every recorded gitlink without
demanding content that has not been fetched. A missing `.gitmodules` entry, a
wrong URL or an absent gitlink still fails.

```bash
python3 scripts/check_graph.py --shallow
```

```bash
python3 scripts/board_status.py
```

A fresh recursive clone was checked when this repository was established: `git
submodule status --recursive` reported 96 entries — 32 boards, 32 toolkits, 32
routers — all clean, with no uninitialised or mismatched gitlink;
`check_graph.py` confirmed all four levels with every board resolving toolkit
`23939912677c` and router `dc2d365ca261`; and `run.py preflight`, run from
inside a board in that clone, reported `READY`. The graph is not only present,
it works from a clone with no manual setup.

## The 32 boards

`Dif` is difficulty, 1–5: how hard the board is. `Det` is brief detail, 1–5: how
much of it the brief states.

Spread — difficulty `1:2 2:6 3:10 4:8 5:6`, detail `1:2 2:9 3:9 4:9 5:3`, across 31 distinct
categories.

| # | Repository | Board | Category | Dif | Det | Layers |
|--:|---|---|---|--:|--:|---|
| 1 | [`PCBA_StatusBeacon`](https://github.com/pentolope/PCBA_StatusBeacon) | Status Beacon Controller | simple-digital | 1 | 1 | 2 |
| 2 | [`PCBA_I2C_EnvSensor`](https://github.com/pentolope/PCBA_I2C_EnvSensor) | I²C Environmental Sensor Pod | sensor | 1 | 2 | 2 |
| 3 | [`PCBA_QuadRelayController`](https://github.com/pentolope/PCBA_QuadRelayController) | Four-Channel Relay Controller | industrial-control | 2 | 2 | 2 |
| 4 | [`PCBA_4Fan_Controller`](https://github.com/pentolope/PCBA_4Fan_Controller) | Four-Fan PWM/Tach Controller | mixed-power-digital | 2 | 1 | 2 |
| 5 | [`PCBA_USB_C_UART_Debugger`](https://github.com/pentolope/PCBA_USB_C_UART_Debugger) | USB-C UART Debug Adapter | high-speed-lite | 2 | 3 | 2 |
| 6 | [`PCBA_CAN_FD_Node`](https://github.com/pentolope/PCBA_CAN_FD_Node) | CAN-FD Sensor/Control Node | industrial-network | 2 | 3 | 2 or 4 |
| 7 | [`PCBA_LiIon_PowerBank`](https://github.com/pentolope/PCBA_LiIon_PowerBank) | Single-Cell Li-Ion Power Bank | power-management | 2 | 2 | 2 or 4 |
| 8 | [`PCBA_StepperController`](https://github.com/pentolope/PCBA_StepperController) | Quiet Stepper Motor Controller | motor-control | 3 | 3 | 4 preferred |
| 9 | [`PCBA_Precision_Thermocouple_DAQ`](https://github.com/pentolope/PCBA_Precision_Thermocouple_DAQ) | Eight-Channel Thermocouple DAQ | precision-analog | 3 | 4 | 4 |
| 10 | [`PCBA_USB_Audio_Interface`](https://github.com/pentolope/PCBA_USB_Audio_Interface) | Stereo USB Audio Interface | audio-mixed-signal | 3 | 3 | 4 |
| 11 | [`PCBA_4_20mA_IO`](https://github.com/pentolope/PCBA_4_20mA_IO) | Four-Channel 4–20 mA I/O Module | industrial-analog | 3 | 4 | 4 |
| 12 | [`PCBA_LoadCell_Instrument`](https://github.com/pentolope/PCBA_LoadCell_Instrument) | Four-Channel Load-Cell Instrument | precision-analog | 3 | 2 | 4 |
| 13 | [`PCBA_RP2040_DevBoard`](https://github.com/pentolope/PCBA_RP2040_DevBoard) | RP2040 Development Board | digital-mcu | 2 | 4 | 2 or 4 |
| 14 | [`PCBA_STM32_SDIO_Logger`](https://github.com/pentolope/PCBA_STM32_SDIO_Logger) | High-Speed SD Data Logger | digital-storage | 3 | 3 | 4 |
| 15 | [`PCBA_Ethernet_RMII_Node`](https://github.com/pentolope/PCBA_Ethernet_RMII_Node) | 100BASE-TX Ethernet Control Node | networking | 3 | 4 | 4 |
| 16 | [`PCBA_FPGA_PMOD_Bridge`](https://github.com/pentolope/PCBA_FPGA_PMOD_Bridge) | Small FPGA Multi-I/O Bridge | fpga | 3 | 2 | 4 |
| 17 | [`PCBA_5A_Synchronous_Buck`](https://github.com/pentolope/PCBA_5A_Synchronous_Buck) | 12 V to 5 V / 5 A Synchronous Buck | power | 3 | 5 | 4 |
| 18 | [`PCBA_3Phase_BLDC_Controller`](https://github.com/pentolope/PCBA_3Phase_BLDC_Controller) | Three-Phase BLDC Motor Controller | power-motor | 4 | 4 | 4 |
| 19 | [`PCBA_PoE_Powered_Node`](https://github.com/pentolope/PCBA_PoE_Powered_Node) | PoE-Powered Ethernet Sensor Node | isolated-power-networking | 4 | 3 | 4 |
| 20 | [`PCBA_Solar_MPPT_Controller`](https://github.com/pentolope/PCBA_Solar_MPPT_Controller) | Solar MPPT Battery Charger | power-energy | 4 | 2 | 4 |
| 21 | [`PCBA_BLE_Sensor_Tag`](https://github.com/pentolope/PCBA_BLE_Sensor_Tag) | BLE Environmental Sensor Tag | rf-low-power | 3 | 4 | 4 |
| 22 | [`PCBA_GNSS_Receiver`](https://github.com/pentolope/PCBA_GNSS_Receiver) | Precision GNSS Receiver | rf-navigation | 4 | 3 | 4 |
| 23 | [`PCBA_SubGHz_Telemetry`](https://github.com/pentolope/PCBA_SubGHz_Telemetry) | Sub-GHz Telemetry Radio | rf-radio | 4 | 2 | 4 |
| 24 | [`PCBA_SDR_IF_Sampler`](https://github.com/pentolope/PCBA_SDR_IF_Sampler) | Wideband IF Sampling Board | mixed-signal-high-speed | 4 | 4 | 6 preferred |
| 25 | [`PCBA_USB3_Hub`](https://github.com/pentolope/PCBA_USB3_Hub) | Four-Port USB 3.x Hub | high-speed-digital | 4 | 4 | 6 |
| 26 | [`PCBA_Gigabit_Ethernet_Switch`](https://github.com/pentolope/PCBA_Gigabit_Ethernet_Switch) | Five-Port Gigabit Ethernet Switch | high-speed-networking | 5 | 3 | 6 |
| 27 | [`PCBA_HDMI_FPGA_Bridge`](https://github.com/pentolope/PCBA_HDMI_FPGA_Bridge) | HDMI-to-FPGA Video Bridge | high-speed-video | 5 | 3 | 6 |
| 28 | [`PCBA_DDR3_FPGA_Controller`](https://github.com/pentolope/PCBA_DDR3_FPGA_Controller) | FPGA with DDR3 Memory | very-high-speed-digital | 5 | 5 | 8 preferred |
| 29 | [`PCBA_Camera_Serializer_Carrier`](https://github.com/pentolope/PCBA_Camera_Serializer_Carrier) | Dual-Camera High-Speed Carrier | camera-high-speed | 5 | 2 | 6 |
| 30 | [`PCBA_Motor_Encoder_Ring`](https://github.com/pentolope/PCBA_Motor_Encoder_Ring) | Circular Multi-Sensor Motor Encoder Ring | mechanical-constrained-sensor | 4 | 4 | 4 |
| 31 | [`PCBA_Dense_MixedSignal_Instrument`](https://github.com/pentolope/PCBA_Dense_MixedSignal_Instrument) | Dense Mixed-Signal Instrument Controller | mixed-signal | 5 | 2 | 6 |
| 32 | [`PCBA_CircularPDM_MicrophoneArray`](https://github.com/pentolope/PCBA_CircularPDM_MicrophoneArray) | 16-Channel Circular PDM Microphone Array | audio-fpga-circular | 5 | 5 | 4 |

## Difficulty and detail are different axes

A low `detail` is not a low bar. A detail-1 brief leaves architecture and
component selection open **on purpose**, and the benchmark's central rule
follows from that:

> Missing details are design freedom, not permission to fabricate unstated user
> requirements.

An agent that fills the silence with invented user requirements has failed the
board more thoroughly than one that designs it badly, because the invented
requirement is unfalsifiable — it looks like a specification. Every board
repository therefore keeps two separate lists: `fixed_requirements`, each bound
to verbatim brief text and a digest of the brief's bytes, and `open_decisions`,
which are the design agent's to make and to record as choices.

See [BENCHMARK.md](BENCHMARK.md) for the attempt protocol.

## Layout

| Path | Contents |
|---|---|
| `boards_index.json` | the catalogue, byte for byte as supplied by the seed pack |
| `BENCHMARK.md` | the attempt protocol: what a run may assume, do and claim |
| `boards/NN_PCBA_*` | the 32 board repositories, as submodules |
| `scripts/check_graph.py` | proves the four-level graph and the catalogue's coherence |
| `scripts/board_status.py` | what each board is and how far it has got |
| `results/` | compact per-attempt results — metrics and verdicts, not build trees |
| `.claude/skills/` | the claim-audit and accountability-review skills [CLAUDE.md](CLAUDE.md) requires before a push |

`boards_index.json` is unmodified, which is why the `brief` path in every entry
resolves inside this checkout: submodule directories are named `NN_RepoName` to
match the seed pack exactly. `check_graph.py` verifies that, rather than
assuming it.

## What is deliberately not here

- **No board build trees.** A board's design lives in the board's repository.
- **No copy of the toolkit or the router.** They are reached through the boards,
  at one pinned commit each.
- **No routing, candidate, build, release or openEMS output.** Those are
  regenerated from what is committed, and are ignored across the whole graph.
- **No designs.** The thirty-two boards are scaffolded from their briefs and not
  yet designed. `scripts/board_status.py` says so per board, and reports a board
  as designed only when a KiCad board file is actually present.
