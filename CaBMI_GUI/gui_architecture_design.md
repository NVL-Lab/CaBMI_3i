# CaBMI GUI Architecture and Design Document

## Overview

The CaBMI GUI provides a unified interface for configuring, managing, and launching CaBMI experiments. The design separates experiment configuration from experiment execution, allowing experimenters to prepare sessions, save configurations, and later execute protocols through a dedicated run window.

The GUI is intended to become the primary interface between experimenters and the CaBMI platform, while remaining extensible to future hardware integrations such as microscope control, holographic stimulation, photopharmacology, behavioral monitoring, and other experimental modules.

---

# Design Philosophy

The GUI is organized around four principles:

1. Separate session selection from object editing.
2. Separate experiment configuration from experiment execution.
3. Make experiment capabilities determine which settings are visible.
4. Store all session information in a structured configuration that can later be saved with experimental data.

The goal is to minimize accidental errors while making it easy to create, reuse, and modify experimental protocols.

---

# Data Hierarchy

The system is organized as:

User
└── Project
├── Animals
├── Experiment Templates
└── Sessions

## User

Represents an individual experimenter.

Each user maintains their own:

* projects
* animals
* experiment templates

Users may optionally copy templates from other users.

---

## Project

A project is the primary organizational unit.

Examples:

* Motor Learning
* Holographic BMI
* Dopamine Learning
* Photopharmacology

A project contains:

* animals
* experiment templates
* session records

Animals belong to a project.

---

## Animal

Animals contain metadata only.

Fields:

* Animal ID
* Sex
* Genotype
* Notes

Examples:

* NVL001
* NVL002
* GG

Animals are selected during session setup.

Animal editing is performed through popup dialogs.

Animal information is not edited directly in the main GUI.

---

## Experiment Templates

Experiment templates define reusable experiment configurations.

A template contains:

* experiment description
* experiment notes
* capabilities
* default settings

Examples:

* default_cabmi
* cabmi_holography
* reward_learning
* photopharm_d1r

Templates are intended to be cloned and modified as protocols evolve.

---

# Capabilities

Capabilities define which modules participate in an experiment.

Capabilities also determine which settings tabs appear in the GUI.

Current capabilities:

* CaBMI
* Imaging
* Auditory Feedback
* Reward
* Random Stimulation
* Holography
* Photopharm
* Behavioral Camera
* External Trigger

Example:

If an experiment enables:

* CaBMI
* Imaging
* Reward

then only those corresponding settings tabs are displayed.

This prevents irrelevant parameters from cluttering the interface.

---

# Main Window Architecture

The main GUI contains three functional regions.

## Left Panel: Session Setup

Purpose:

Select what session will be run.

Contains:

* User
* Project
* Animal
* Date
* Day
* Save Path
* Pre-session Notes
* Status Log

Actions:

* Create User
* Create Project
* Create Animal
* Clone Animal
* Edit Animal
* Preview Config
* Save Config
* Launch CaBMI

The left panel does not contain experiment editing.

---

## Right Top Panel: Experiment Template

Purpose:

Configure the experiment template.

Contains:

* Template Selection
* Description
* Notes
* Capabilities

Actions:

* Load Template
* Save Template
* Save As New Template

Templates define the default experiment configuration.

Loading a template automatically:

* loads capabilities
* loads settings values
* updates visible settings tabs

---

## Right Bottom Panel: Settings

Purpose:

Display settings associated with active capabilities.

Tabs appear dynamically.

Examples:

* CaBMI
* Imaging
* Auditory Feedback
* Reward
* Holography
* Photopharm

Additional capabilities automatically create additional settings sections.

A Custom tab is provided for temporary or experimental parameters that do not yet have dedicated GUI support.

---

# Session Configuration

The GUI generates a session configuration object containing:

* user
* project
* animal
* experiment template
* settings
* capabilities
* session metadata

The configuration can be:

* previewed
* saved
* used to launch a session

---

# Preview Config

Preview Config displays a human-readable summary of the current session.

Purpose:

Allow experimenters to verify settings before running an experiment.

The preview summarizes:

* session metadata
* animal information
* active capabilities
* settings values
* notes

This is intended for experimenters, not developers.

---

# Save Config

Save Config writes the session configuration to disk.

Purpose:

* preserve experiment settings
* enable reproducibility
* allow future inspection
* provide input for experiment execution

Saving a configuration does not launch the experiment.

---

# Future Session Execution Window

The main configuration window is not responsible for executing experiments.

Pressing Launch CaBMI will open a dedicated Run Session window.

The Run Session window will execute the protocol step-by-step.

Example workflow:

1. Initialize Session
2. Acquire ROI Background
3. Acquire ROI Data
4. Acquire Baseline
5. Select Ensembles
6. Calibrate Target
7. Start BMI
8. End Session

Each step will display:

* status
* completion state
* relevant outputs

Experimenters will be able to repeat steps when necessary.

---

# Capability-Dependent Execution

Capabilities may insert additional protocol steps.

Examples:

Reward:

* Test reward device

Auditory Feedback:

* Test audio feedback

Holography:

* Calibrate holographic targets

Photopharm:

* Verify stimulation protocol

Behavior Camera:

* Verify camera recording

Thus, the execution workflow is generated dynamically from the experiment configuration.

---

# Future Hardware Integration

Planned future integrations include:

* 3i microscope control
* Slidebook interaction
* Holographic stimulation control
* Photopharmacology control
* Behavioral camera control
* NWB data integration

These integrations should remain independent modules accessed through the execution workflow.

The configuration GUI should remain responsible only for experiment setup and configuration management.
