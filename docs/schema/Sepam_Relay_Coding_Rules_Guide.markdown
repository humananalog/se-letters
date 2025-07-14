# Guideline Document for Sepam Protection Relays Coding Rules

## Purpose
This document provides a comprehensive guide for an AI coding tool to interpret, validate, and generate nomenclature codes for Schneider Electric’s Sepam protection relays. The Sepam coding system defines the relay’s series, application, protection functions, hardware configurations, communication interfaces, and other options. This guide ensures accurate processing of Sepam codes for automation, configuration, and ordering purposes, adhering to Schneider Electric’s standards.

## Overview of Sepam Coding Rules
Sepam relays are organized into series (e.g., Series 10, 20, 40, 60, 80), each designed for specific applications and complexity levels. The nomenclature code is a structured alphanumeric string that encapsulates the relay’s model, application type, and configuration details. The code is used in product catalogs, ordering forms, and configuration tools like SFT2841. The structure varies by series but typically includes fields for the series, application, and additional options.

### General Structure
A Sepam code typically follows a format like `SP-59607-S20-8-9` or `SEPAM S80`, where:
- **SP-59607**: Part number or catalog reference (optional, used in ordering).
- **S20**: Model and application (e.g., Series 20, substation protection).
- **8**: Hardware or firmware option (e.g., specific I/O configuration).
- **9**: Additional options (e.g., communication protocol or language).

The exact structure depends on the Sepam series and is detailed in product-specific documentation (e.g., Sepam Series 20, 40, 60, 80).[](https://elec-engg.com/sepam-protection-relays/)[](https://www.se.com/au/en/product-range/933-sepam-series-20/)[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)

## Key Components of Sepam Codes
The following sections outline the primary fields in Sepam nomenclature codes, based on Schneider Electric’s documentation for Series 10, 20, 40, 60, and 80.

### 1. Series Designation
- **Description**: Identifies the Sepam series, which determines the relay’s complexity and target application.
- **Examples**:
  - **Series 10**: Basic protection for medium voltage (MV) networks (e.g., Sepam 10N).[](https://dsgenterprisesltd.com/integrating-schneider-sepam-series-10-n-relays-into-substation-automation-systems/)
  - **Series 20**: Standard protection for distribution systems (e.g., S20, T20, M20).[](https://www.se.com/au/en/product-range/933-sepam-series-20/)[](https://dsgenterprisesltd.com/product/schneider-sepam-20n-protection-relays/)
  - **Series 40**: Demanding applications with enhanced features.[](https://www.se.com/us/en/product-range/934-sepam-series-40/)
  - **Series 60**: Complex distribution systems (e.g., S60, T60, G60).[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
  - **Series 80**: Advanced applications with custom protection (e.g., S80, S81, T81).[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)[](https://dsgenterprisesltd.com/product/schneider-sepam-80-protection-relays/)
- **AI Tool Action**:
  - Validate the series against supported Sepam models.
  - Map the series to its intended application (e.g., Series 10 for secondary distribution, Series 80 for advanced protection).

### 2. Application Type
- **Description**: Specifies the primary application of the relay, such as substation, transformer, motor, generator, or capacitor protection.
- **Examples** (from Series 20, 60, 80 documentation):
  - **S**: Substation protection (e.g., S20, S60, S80).
  - **T**: Transformer protection (e.g., T20, T60, T81).
  - **M**: Motor protection (e.g., M20, M61).
  - **G**: Generator protection (e.g., G60, G62).
  - **B**: Busbar protection (e.g., B21, B22).
  - **C**: Capacitor protection (e.g., C60, C86).
- **AI Tool Action**:
  - Ensure the application code matches the series (e.g., `C60` is valid for Series 60, but not Series 20).
  - Cross-reference with protection functions (e.g., `S80` includes directional overcurrent and earth fault).[](https://elec-engg.com/sepam-protection-relays/)[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)

### 3. Specific Model Variant
- **Description**: Indicates specific protection functions or configurations within the application type.
- **Examples**:
  - **Series 20**: `S20` (basic substation), `S24` (substation with overload), `T24` (transformer with directional overcurrent).[](https://www.se.com/au/en/product-range/933-sepam-series-20/)
  - **Series 60**: `S62` (substation with overload and directional overcurrent), `T62` (transformer with directional earth fault).[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
  - **Series 80**: `S81` (substation with overload and directional earth fault), `S84` (substation with active over/under power).[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)
- **AI Tool Action**:
  - Validate the model variant against the series and application.
  - Ensure compatibility with protection functions (e.g., `S84` requires active over/under power support).

### 4. Hardware Configuration
- **Description**: Defines the hardware setup, including input/output (I/O) modules, connectors, and sensors (e.g., core balance CT).
- **Examples** (from Series 20, 60, 80):
  - **Base Unit**: Includes one base unit with 20-pin connectors and current/voltage connectors.[](https://dsgenterprisesltd.com/product/schneider-sepam-20n-protection-relays/)
  - **I/O Modules**: MES114F (10 inputs, 4 outputs) for Series 20/40/80.[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
  - **Temperature Sensors**: MET148-2 (8 inputs for temperature monitoring).[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
- **AI Tool Action**:
  - Verify that the hardware configuration is compatible with the series and model (e.g., MES114F for Series 80).
  - Check for mandatory components (e.g., current connector for `S20`).

### 5. Communication Interface
- **Description**: Specifies the communication protocol for integration with SCADA or substation automation systems.
- **Examples**:
  - **Modbus**: Supported across Series 10, 20, 40, 60, 80.[](https://www.productinfo.schneider-electric.com/nadigest/5c51d645347bdf0001f1f280/Master/17705_MAIN%2520%28bookmap%29_0000054913.xml/%24/SepamProtectionRelaysCPT_0000285567)
  - **IEC 61850**: Supported in Series 40, 60, 80 for smart grid integration.[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)
  - **DNP3**: Available in Series 80 for advanced applications.[](https://www.productinfo.schneider-electric.com/nadigest/5c51d645347bdf0001f1f280/Master/17705_MAIN%2520%28bookmap%29_0000054913.xml/%24/SepamProtectionRelaysCPT_0000285567)
  - **RS485 Interface**: ACE919CA for Series 20/40/80.[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
- **AI Tool Action**:
  - Validate the communication protocol against the series (e.g., IEC 61850 not supported in Series 10).
  - Ensure compatibility with network requirements (e.g., Modbus for legacy systems).

### 6. Language and Firmware Options
- **Description**: Defines the operating language for the human-machine interface (HMI) and firmware features (e.g., TCP/IP support).
- **Examples**:
  - **Language**: English, French, Spanish, or Chinese (configurable via SFT2841).[](https://turbofuture.com/industrial/Set-Program-Schneider-Electric-Sepam-S20-Relay)
  - **Firmware**: TCP/IP firmware option for Series 60/80.[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
- **AI Tool Action**:
  - Ensure the language option is valid for the HMI and region.
  - Validate firmware compatibility with the series and communication options.

### 7. Additional Options
- **Description**: Includes optional features such as memory cartridges, core balance CT, or specific protection settings (e.g., Zone Selective Interlocking [ZSI]).
- **Examples**:
  - **Memory Cartridge**: Removable cartridge for quick configuration replacement in Series 80.[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)
  - **ZSI**: Supported in Series 20, 40, 60, 80 for motor and substation applications.[](https://dsgenterprisesltd.com/product/schneider-sepam-80-protection-relays/)
  - **Core Balance CT**: ACE990 interface for Series 20/40/80.[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
- **AI Tool Action**:
  - Verify that additional options are supported by the series and model.
  - Flag deprecated or incompatible options (e.g., ZSI not available in Series 10).

## Guidelines for AI Coding Tool
The AI tool must process Sepam codes accurately to support automation, validation, and generation tasks. The following guidelines ensure reliable handling of Sepam nomenclature codes:

### 1. Validation
- **Input Parsing**: Parse the Sepam code into its constituent fields (e.g., series, application, hardware, communication).
- **Field Validation**:
  - Check each field against a database of valid values for the specific series (e.g., `S20` for Series 20, `S80` for Series 80).
  - Ensure compatibility between fields (e.g., IEC 61850 requires Series 40 or higher).[](https://www.productinfo.schneider-electric.com/nadigest/5c51d645347bdf0001f1f280/Master/17705_MAIN%2520%28bookmap%29_0000054913.xml/%24/SepamProtectionRelaysCPT_0000285567)
- **Error Handling**:
  - Flag invalid codes (e.g., `S10` is not a valid model).
  - Provide descriptive error messages (e.g., “Invalid application ‘C’ for Series 20”).

### 2. Generation
- **Code Construction**:
  - Start with the series and application (e.g., `S20` for substation protection).
  - Append hardware, communication, and additional options based on user input or defaults.
  - Include part numbers (e.g., `SP-59607`) if required for ordering.[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
- **Default Values**:
  - Use common configurations as defaults (e.g., Modbus for communication, English for HMI).
  - Prompt for clarification if critical fields (e.g., application type) are unspecified.
- **Output Format**:
  - Generate the Sepam code as a single string (e.g., `SP-59607-S20-8-9`).
  - Provide a human-readable breakdown of each field (e.g., Series: 20, Application: Substation, Communication: Modbus).

### 3. Database Integration
- **Maintain a Database**:
  - Store valid Sepam series, models, and options (e.g., Series 20: S20, S24, T20; Series 80: S80, S81, S84).
  - Update the database with new models or changes, as Sepam products evolve.[](https://dsgenterprisesltd.com/how-schneider-sepam-series-80-enhances-power-system-protection-and-reliability/)[](https://dsgenterprisesltd.com/product/schneider-sepam-80-protection-relays/)
- **Cross-Reference**:
  - Map codes to specifications (e.g., `S80` to substation protection with IEC 61850).
  - Support legacy models (e.g., Series 10 for refurbishment projects).[](https://dsgenterprisesltd.com/integrating-schneider-sepam-series-10-n-relays-into-substation-automation-systems/)

### 4. Compatibility Checks
- **Hardware/Software Compatibility**:
  - Verify that hardware options (e.g., MES114F) are compatible with the series and model.[](https://www.kvc.com.my/Products/Automation-and-Control/Relays/Control-and-Measurement-Relay/Protection-Relay/)
  - Ensure firmware supports selected communication protocols (e.g., TCP/IP for Series 80).[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
- **Application Context**:
  - Ensure the code matches the intended application (e.g., `T60` for transformer protection, `M61` for motor protection).[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
- **Configuration Tool Integration**:
  - Support compatibility with SFT2841 configuration software for parameter setup (e.g., overcurrent, earth fault settings).[](https://turbofuture.com/industrial/Set-Program-Schneider-Electric-Sepam-S20-Relay)

### 5. Documentation and Reporting
- **Generate Reports**:
  - Produce a detailed report for each Sepam code, listing the series, application, hardware, communication, and additional options.
  - Include warnings for deprecated options or configurations requiring specific advice (e.g., Series 10 limitations).[](https://dsgenterprisesltd.com/integrating-schneider-sepam-series-10-n-relays-into-substation-automation-systems/)
- **User Assistance**:
  - Suggest alternative configurations if a code is invalid (e.g., recommend `S80` instead of `S20` for IEC 61850).
  - Link to Schneider Electric’s Sepam configurator tools or documentation for further reference (e.g., https://www.se.com).[](https://www.se.com/us/en/product-range/934-sepam-series-40/)[](https://www.se.com/au/en/product-range/933-sepam-series-20/)

## Example Implementation
Below is a sample pseudocode for an AI tool to validate and generate a Sepam code for a Series 20 relay:

```python
# Database of valid options for Sepam Series 20
SEPAM_S20_OPTIONS = {
    "series": ["10", "20", "40", "60", "80"],
    "application": ["S20", "S24", "T20", "T24", "M20", "B21", "B22"],
    "hardware": ["MES114F", "MET148-2", "ACE990"],
    "communication": ["Modbus", "IEC61850", "DNP3"],
    "language": ["English", "French", "Spanish", "Chinese"],
    "options": ["ZSI", "CoreBalanceCT"]
}

def validate_sepam_code(code):
    # Parse code (e.g., SP-59607-S20-8-9)
    part_number, model, hardware, options = parse_sepam_code(code)
    
    # Validate each field
    if model not in SEPAM_S20_OPTIONS["application"]:
        return False, "Invalid application model"
    if hardware not in SEPAM_S20_OPTIONS["hardware"]:
        return False, "Invalid hardware configuration"
    # ... validate other fields ...
    
    return True, "Valid Sepam code"

def generate_sepam_code(series, user_config):
    # Default configuration
    config = {
        "application": "S20",
        "hardware": "MES114F",
        "communication": "Modbus",
        "language": "English",
        "options": []
    }
    
    # Update with user-specified config
    config.update(user_config)
    
    # Construct code
    part_number = "SP-59607" if series == "20" else f"SP-{series}XXX"
    code = f"{part_number}-{config['application']}-8-9"
    
    # Validate
    is_valid, message = validate_sepam_code(code)
    if not is_valid:
        raise ValueError(message)
    
    return code, {
        "Series": series,
        "Application": config['application'],
        "Hardware": config['hardware'],
        "Communication": config['communication'],
        "Language": config['language'],
        "Options": config['options']
    }

# Example usage
code, details = generate_sepam_code("20", {"application": "S20", "communication": "Modbus"})
print(f"Sepam Code: {code}")
print("Details:", details)
```

**Output**:
```
Sepam Code: SP-59607-S20-8-9
Details: {
    "Series": "20",
    "Application": "S20",
    "Hardware": "MES114F",
    "Communication": "Modbus",
    "Language": "English",
    "Options": []
}
```

## References
- Schneider Electric Sepam Series 20, 40, 60, 80 Catalog and Datasheets.[](https://elec-engg.com/sepam-protection-relays/)[](https://www.se.com/au/en/product-range/933-sepam-series-20/)[](https://dsgenterprisesltd.com/product/schneider-sepam-60-protection-relays/)
- Sepam Series 10N Integration in Substation Automation Systems.[](https://dsgenterprisesltd.com/integrating-schneider-sepam-series-10-n-relays-into-substation-automation-systems/)
- SFT2841 Configuration Software Guide for Sepam Relays.[](https://turbofuture.com/industrial/Set-Program-Schneider-Electric-Sepam-S20-Relay)
- Sepam Series 80 Ordering Configurations, Schneider Electric Digest Plus.

## Notes
- Sepam relays are continuously updated, so specifications may change. Always consult the latest Schneider Electric documentation for updates.
- For complex configurations or specific applications, contact Schneider Electric experts or refer to the SFT2841 configuration tool for tailored advice.[](https://www.se.com/us/en/product-range/934-sepam-series-40/)