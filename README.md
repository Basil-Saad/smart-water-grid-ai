# IoT-Based Smart Water Grid Management System with AI Predictive Analytics
![Python](https://img.shields.io/badge/Python-3.x-blue)
![ESP32](https://img.shields.io/badge/ESP32-IoT-red)
![Arduino](https://img.shields.io/badge/Arduino-IDE-00979D)
![AI](https://img.shields.io/badge/AI-XGBoost-green)
![Firebase](https://img.shields.io/badge/Firebase-Cloud-orange)

An AI-powered IoT platform for real-time water distribution monitoring, leakage detection, predictive analytics, intelligent water demand forecasting, and remote infrastructure management.

<p align="center">
  <img src="images/hero/system-overview.jpg" width="80%">
</p>

## Project Highlights

- 📡 Real-time IoT Monitoring
- 🤖 AI-based Water Demand Prediction
- 💧 Automatic Leakage Detection
- ☁️ Cloud Dashboards
- 🌐 Digital Twin Simulation

| Category | Details |
|----------|---------|
| Platform | IoT Smart Water Grid |
| Microcontroller | ESP32 |
| Programming | Arduino IDE, Python, HTML/CSS, JavaScript |
| AI Model | XGBoost |
| Cloud | Firebase |
| Dashboard | Company & Customer Web Dashboards |

## Overview

Water distribution networks face increasing challenges in infrastructure monitoring, leakage detection, and efficient resource management. Traditional monitoring methods often rely on manual inspection and provide limited real-time visibility, making it difficult to detect faults early and optimize water consumption.

This project presents an **IoT-Based Smart Water Grid Management System with AI Predictive Analytics** that integrates distributed ESP32-based sensing nodes, cloud connectivity, predictive analytics, and interactive web dashboards into a unified intelligent platform. The system continuously monitors water distribution, detects leakages, forecasts future water demand using an XGBoost machine learning model, and provides real-time visualization for both the water company and customers.

By integrating IoT, cloud computing, machine learning, and digital twin simulation, the proposed platform delivers an end-to-end intelligent water management solution that improves operational efficiency, minimizes water losses, supports predictive maintenance, and enables data-driven decision-making.

## System Architecture

The proposed platform consists of three distributed ESP32-based sensing nodes connected to a cloud platform, an AI prediction server, and two web dashboards for monitoring and management.

The architecture enables real-time data acquisition, cloud synchronization, AI-based demand forecasting, leakage detection, and remote visualization for both the water company and customers.

<p align="center">
  <img src="images/architecture/system-architecture.jpg" width="900">
</p>

<p align="center"><em>Overall system architecture.</em></p>

<p align="center">
  <img src="images/architecture/data-flow.jpg" width="900">
</p>

<p align="center"><em>System data flow.</em></p>

## System Components

The proposed smart water grid management system integrates hardware, cloud services, AI analytics, and web applications into a unified platform. Three ESP32 sensor nodes collect real-time data from the water network and communicate exclusively through the Firebase Realtime Database, which acts as the central communication hub between all system components. The cloud infrastructure stores sensor data, synchronizes actuator commands, and provides data for visualization and AI-based demand prediction.

| Component | Description |
|-----------|-------------|
| **ESP32 Node 1 (Company Side)** | Monitors water level, flow rate, water quality (TDS), and pipeline pressure, while controlling the water pump and company-side solenoid valve. |
| **ESP32 Nodes 2 & 3 (Customer Side)** | Measure customer water consumption using flow sensors and control individual solenoid valves for water distribution. |
| **Firebase Realtime Database** | Central communication hub that stores sensor readings, synchronizes actuator commands, and connects all ESP32 nodes, dashboards, and AI services. |
| **AI Prediction Module (XGBoost)** | Predicts future water demand using historical datasets generated from the digital twin simulation. |
| **Company Dashboard** | Displays real-time system status, sensor values, alerts, historical trends, and provides remote actuator control. |
| **Customer Dashboard** | Allows customers to monitor water usage, consumption history, and billing information in real time. |
| **Digital Twin Simulation** | Python-based simulator that generates realistic water consumption datasets for AI model training and evaluation. |

## Hardware Prototype

The hardware prototype demonstrates the practical implementation of the proposed smart water grid management system. It consists of three ESP32-based sensing nodes integrated with water level, flow rate, water quality, and pressure sensing, along with relay-controlled actuators, solenoid valves, and a water pump. The prototype validates real-time monitoring, automatic control, cloud communication, and leakage detection in a realistic environment.

### Prototype Overview

<p align="center">
  <img src="images/hardware/prototype-top-view.jpg" alt="Prototype Top View" width="350">
</p>

<p align="center">
<b>Figure 1.</b> Top view of the implemented smart water grid prototype.
</p>

### Leakage Detection Branch

<p align="center">
  <img src="images/hardware/leakage-branch.jpg" alt="Leakage Detection Branch" width="250">
</p>

<p align="center">
<b>Figure 2.</b> Experimental leakage branch used to simulate pipeline leaks and evaluate the leakage detection mechanism.
</p>
