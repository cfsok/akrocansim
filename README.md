# akrocansim
A CAN bus J1939 controller simulator.

[![Downloads](https://static.pepy.tech/badge/akrocansim)](https://pepy.tech/project/akrocansim)
[![Downloads](https://static.pepy.tech/badge/akrocansim/month)](https://pepy.tech/project/akrocansim)

## Built with
- [python-can](https://github.com/hardbyte/python-can)
- [DearPyGUI](https://github.com/hoffstadt/DearPyGui)
- [openpyxl](https://openpyxl.readthedocs.io/)

## Features
- Integrates with all hardware CAN interfaces supported by python-can.
- Transmits configured J1939 PGNs to the CAN bus with the following methods:
  - continuous tx of all PGNs
  - all PGNs transmitted once on button press
  - per PGN transmission, either continuous or on button press
- GUI for setting SPN values:
  - sliders for changing continuous values
  - label selection for discrete values
  - direct entry of raw decimal values
  - direct entry of decoded decimal values

![Akrocansim demo screenshot 1](https://raw.githubusercontent.com/cfsok/akrocansim/main/docs/images/demo_1_Akrocansim.png)

![Akrocansim demo screenshot 2](https://raw.githubusercontent.com/cfsok/akrocansim/main/docs/images/demo_2_Akrocansim.png)

![PCAN-View demo screenshot 1](https://raw.githubusercontent.com/cfsok/akrocansim/main/docs/images/demo_1_PCAN-View.png)

## Installation
Python 3.11 (64-bit) or higher is required.

```pip install akrocansim```

## Prerequisites
- A hardware CAN interface supported by python-can (support for virtual interfaces could be added - let me know),
see https://python-can.readthedocs.io/en/v4.3.1/interfaces.html.
- A version of J1939 Digital Annex (J1939DA) from SAE International, see https://www.sae.org/standards/?search=j1939DA.
- A way to reliably convert `.xls` to `.xlsx` if your copy of the J1939DA is in `.xls` format
(Microsoft Excel obviously works, but I am not sure of third party tool).

## Usage
```python -m akrocansim```

Upon initial run, an `akrocansim` folder is created in your home folder hosting a starting configuration file.

Follow the instructions on the application and in the configuration file for next steps.

Upon successful parsing of the J1939DA, a series of json files are created in the `J1939` sub-folder inside the main configuration folder.
These can be inspected to evaluate parsing correctness.

The J1939DA PGN and SPN definition format is very irregular and parsing errors still exist.
You can raise a GitHub issue or a pull request if you think that an SPN has not been parsed correctly.

## Discussion
Please raise issues or feature requests, or ask questions, using the [GitHub issue tracker](https://github.com/cfsok/akrocansim/issues).
