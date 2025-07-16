# Guideline Document for MiCOM Protection Relays CORTEC Code Nomenclature

## Purpose
This document provides a comprehensive guide for an AI coding tool to interpret, validate, and generate CORTEC codes for MiCOM protection relays. The CORTEC code is a structured alphanumeric string that defines the configuration of a MiCOM relay, including its model, electrical specifications, hardware, software, communication interfaces, and mounting options. This guide ensures accurate processing of CORTEC codes for automation, configuration, and ordering purposes.

## Overview of CORTEC Code Nomenclature
The CORTEC (Configuration and Ordering Technical Code) is a modular, position-based code that specifies the characteristics of MiCOM protection relays. Each position in the code represents a specific attribute, such as relay type, input ratings, communication protocols, or mounting options. The code is typically displayed on the relay’s front panel and is used for identification, configuration, and ordering.

### General Structure
A CORTEC code is a sequence of characters (letters and numbers) divided into fields, each representing a specific parameter. The structure varies slightly depending on the MiCOM relay series (e.g., P12x, P14x, P44x, P64x). A typical CORTEC code might look like this:

**Example**: `P441J1M0`
- **P441**: Relay model (e.g., P441 distance protection relay).
- **J**: Design suffix (hardware/software version).
- **1**: Input configuration (e.g., current/voltage ratings).
- **M**: Mounting option (e.g., flush panel mounting).
- **0**: Language or communication option.

The exact structure and options depend on the relay series and model, as detailed in product-specific documentation.

## Key Components of CORTEC Codes
The following sections outline the common fields in a CORTEC code, based on information from MiCOM relay documentation. Each field is position-specific and has a defined set of valid values.

### 1. Relay Model (Positions 1–4 or 1–5)
- **Description**: Identifies the specific MiCOM relay model, indicating its primary function (e.g., distance protection, transformer protection, feeder management).
- **Examples**:
  - `P120`, `P121`, `P122`, `P123`: Overcurrent protection relays.
  - `P441`, `P442`, `P444`: Distance protection relays.
  - `P632`, `P642`, `P643`: Transformer protection relays.
  - `P921`, `P922`: Voltage protection relays.
- **AI Tool Action**:
  - Validate the model code against a predefined list of MiCOM relay models.
  - Map the model to its intended application (e.g., `P441` → distance protection).

### 2. Design Suffix (Position 5 or next)
- **Description**: Indicates the hardware and software version or design generation of the relay. This ensures compatibility with other system components.
- **Examples**:
  - `J`: Modern design with specific software version (e.g., version 32 or later).
  - `B`, `C`: Older design suffixes for compatibility with legacy systems.
- **AI Tool Action**:
  - Check compatibility between the design suffix and the relay model.
  - Ensure the suffix aligns with supported hardware/software versions (e.g., `J` for software version 32+ in P341 relays).

### 3. Input Configuration (Current/Voltage Ratings)
- **Description**: Specifies the electrical input ratings, such as nominal current (`In`), voltage (`Vn`), or auxiliary voltage.
- **Examples** (from P341, P921, P632 documentation):
  - `1`: `In = 1/5A`, `Vn = 100–120Vac`, standard input module.
  - `2`: `In = 1/5A`, `Vn = 380–480Vac`, standard input module.
  - `3`: `In = 1/5A`, `Vn = 100–120Vac`, extended input module.
- **AI Tool Action**:
  - Validate input ratings against the relay model’s supported configurations.
  - Ensure compatibility with the application (e.g., transmission lines require specific voltage ratings).

### 4. Hardware Options (I/O, Case Size)
- **Description**: Defines the number of opto-isolated inputs (optos), relay outputs, and case size (e.g., Size 8, Size 12).
- **Examples** (from P341 documentation):
  - `A`: Size 8 case, 8 optos + 7 relays.
  - `C`: Size 8 case, 16 optos + 7 relays.
  - `E`: Size 12 case, 16 optos + 16 relays.
- **AI Tool Action**:
  - Verify that the hardware configuration matches the relay model and case size.
  - Check for valid combinations (e.g., `E` requires a Size 12 case).

### 5. Communication Interface
- **Description**: Specifies the communication protocol and interface for the relay’s rear communication port.
- **Examples**:
  - `0`: No rear communication.
  - `1`: Modbus.
  - `2`: IEC 61850 (Ethernet).
  - `3`: DNP3.
- **AI Tool Action**:
  - Validate the communication option against the relay’s supported protocols.
  - Ensure compatibility with modern standards (e.g., IEC 61850 for P44x relays).

### 6. Language Options
- **Description**: Defines the language for the relay’s human-machine interface (HMI) and communication ports.
- **Examples** (from P341, P921 documentation):
  - `0`: English, French, German, Spanish.
  - `5`: English, French, German, Russian.
  - `C`: Chinese, English, or French via HMI (English/French via communication port).
- **AI Tool Action**:
  - Ensure the language code is valid for the relay model.
  - Flag potential regional requirements (e.g., Chinese for specific markets).

### 7. Mounting Options
- **Description**: Specifies how the relay is mounted in the panel or rack.
- **Examples**:
  - `M`: Flush panel mounting.
  - `P`: Flush panel mounting with harsh environment coating.
- **AI Tool Action**:
  - Validate the mounting option against the relay’s physical design.
  - Suggest `P` for environments with corrosive gases (e.g., H2S, SO2).

### 8. Additional Options
- **Description**: Includes optional features such as power supply type, software features, or specific configurations (e.g., transient bias for P64x relays).
- **Examples**:
  - Power supply: `C` (improved power supply for P341).
  - Software features: Transient bias, CT supervision, or autoreclose.
- **AI Tool Action**:
  - Cross-check additional options with the relay model’s capabilities.
  - Ensure no conflicts (e.g., transient bias only for P64x series).

## Guidelines for AI Coding Tool
The AI tool must process CORTEC codes accurately to support automation, validation, and generation tasks. The following guidelines ensure reliable handling of CORTEC codes:

### 1. Validation
- **Input Parsing**: Parse the CORTEC code into its constituent fields based on the relay model’s structure.
- **Field Validation**:
  - Check each field against a database of valid values for the specific relay model (e.g., P441, P632).
  - Ensure compatibility between fields (e.g., design suffix `J` requires software version 32+).
- **Error Handling**:
  - Flag invalid codes (e.g., unsupported communication protocol).
  - Provide descriptive error messages (e.g., “Invalid input configuration ‘5’ for P441 relay”).

### 2. Generation
- **Code Construction**:
  - Start with the relay model (e.g., `P441`).
  - Append fields based on user-specified or default configurations.
  - Ensure each field adheres to the model’s valid options.
- **Default Values**:
  - Use common configurations as defaults (e.g., `M` for flush panel mounting, `0` for standard language options).
  - Prompt for clarification if critical fields (e.g., input ratings) are unspecified.
- **Output Format**:
  - Generate the CORTEC code as a single string (e.g., `P441J1M0`).
  - Include a human-readable breakdown of each field for clarity.

### 3. Database Integration
- **Maintain a Database**:
  - Store valid CORTEC field values for each MiCOM relay model (e.g., P12x, P44x, P64x).
  - Update the database with new models or changes, as MiCOM products are subject to continuous development.[](https://www.scribd.com/document/147831078/P922-Cortec)[](https://www.scribd.com/document/443403909/3-P12xy-Sauf-P124-Code-CORTEC)[](https://www.scribd.com/document/152456602/P341-cortec)
- **Cross-Reference**:
  - Map CORTEC codes to relay specifications (e.g., voltage ratings, communication protocols).
  - Support legacy models (e.g., Alstom or AREVA-branded relays) for refurbishment purposes.[](https://www.gevernova.com/grid-solutions/automation/protection-control-metering/line-protection/micom-agile-p441-p442-p444)

### 4. Compatibility Checks
- **Hardware/Software Compatibility**:
  - Verify that the design suffix aligns with the software version and hardware options (e.g., `J` for P341 requires software version 32+).[](https://www.scribd.com/document/152456602/P341-cortec)
- **Application Context**:
  - Ensure the CORTEC code matches the intended application (e.g., `P441` for transmission line protection, `P632` for transformer protection).
- **Refurbishment Support**:
  - Translate legacy CORTEC codes to modern equivalents for upgrades (e.g., from Alstom blue case relays to GE MiCOM P40 series).[](https://www.gevernova.com/grid-solutions/automation/protection-control-metering/line-protection/micom-agile-p441-p442-p444)

### 5. Documentation and Reporting
- **Generate Reports**:
  - Produce a detailed report for each CORTEC code, listing the relay model, input ratings, hardware options, communication protocols, and mounting details.
  - Include warnings for deprecated options or configurations requiring specific advice.[](https://www.scribd.com/document/147831078/P922-Cortec)[](https://www.scribd.com/document/147833069/P921-Cortec)
- **User Assistance**:
  - Provide suggestions for alternative configurations if a code is invalid or suboptimal.
  - Link to Schneider Electric’s CORTEC configurator tools for further reference (e.g., https://www.se.com).[](https://www.se.com/fr/fr/download/document/NRJED311282EN/)[](https://www.se.com/au/en/download/document/NRJED311290EN/)

## Example Implementation
Below is a sample pseudocode for an AI tool to validate and generate a CORTEC code for a MiCOM P441 relay:

```python
# Database of valid options for P441
P441_OPTIONS = {
    "model": ["P441", "P442", "P444"],
    "design_suffix": ["J", "B", "C"],
    "input_config": ["1", "2", "3", "4"],
    "hardware": ["A", "C", "E"],
    "communication": ["0", "1", "2", "3"],
    "language": ["0", "5", "C"],
    "mounting": ["M", "P"]
}

def validate_cortec(code):
    # Parse code (e.g., P441J1M0)
    model, suffix, input_conf, hardware, comm, lang, mount = parse_cortec(code)
    
    # Validate each field
    if model not in P441_OPTIONS["model"]:
        return False, "Invalid relay model"
    if suffix not in P441_OPTIONS["design_suffix"]:
        return False, "Invalid design suffix"
    # ... validate other fields ...
    
    return True, "Valid CORTEC code"

def generate_cortec(model, user_config):
    # Default configuration
    config = {
        "design_suffix": "J",
        "input_config": "1",
        "hardware": "A",
        "communication": "0",
        "language": "0",
        "mounting": "M"
    }
    
    # Update with user-specified config
    config.update(user_config)
    
    # Construct code
    code = f"{model}{config['design_suffix']}{config['input_config']}{config['hardware']}{config['communication']}{config['language']}{config['mounting']}"
    
    # Validate
    is_valid, message = validate_cortec(code)
    if not is_valid:
        raise ValueError(message)
    
    return code, {
        "Model": model,
        "Design Suffix": config['design_suffix'],
        "Input Configuration": config['input_config'],
        "Hardware": config['hardware'],
        "Communication": config['communication'],
        "Language": config['language'],
        "Mounting": config['mounting']
    }

# Example usage
code, details = generate_cortec("P441", {"communication": "2", "mounting": "P"})
print(f"CORTEC Code: {code}")
print("Details:", details)
```

**Output**:
```
CORTEC Code: P441J1A2P
Details: {
    "Model": "P441",
    "Design Suffix": "J",
    "Input Configuration": "1",
    "Hardware": "A",
    "Communication": "2",
    "Language": "0",
    "Mounting": "P"
}
```

## References
- Schneider Electric MiCOM P14x, P63x, P64x Order Form CORTEC Configurators.[](https://www.se.com/fr/fr/download/document/NRJED311282EN/)[](https://www.se.com/au/en/download/document/NRJED311290EN/)[](https://www.se.com/au/en/download/document/NRJED311291EN/)
- GE Vernova MiCOM Agile P441, P442, P444 Documentation.[](https://www.gevernova.com/grid-solutions/automation/protection-control-metering/line-protection/micom-agile-p441-p442-p444)
- MiCOM P12x/y, P921, P922, P632 CORTEC Documents.[](https://www.scribd.com/document/147831078/P922-Cortec)[](https://www.scribd.com/document/443403909/3-P12xy-Sauf-P124-Code-CORTEC)[](https://www.scribd.com/document/147833069/P921-Cortec)

## Notes
- MiCOM relays are subject to continuous development, so product specifications may change. Always consult the latest documentation for updates.[](https://www.scribd.com/document/147831078/P922-Cortec)[](https://www.scribd.com/document/147833069/P921-Cortec)
- For specific configurations or complex applications, contact Schneider Electric or GE Vernova experts for tailored advice.[](https://www.se.com/fr/fr/download/document/NRJED311282EN/)[](https://www.se.com/au/en/download/document/NRJED311290EN/)