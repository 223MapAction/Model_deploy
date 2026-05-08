# 🏗️ Map Action Impact Engine - Architecture & Integration Flow

This document presents the complete technical architecture and integration flow of the Map Action platform. It is designed for technical meetings to illustrate how field data (Image, GPS, Voice) is processed through various AI and Geospatial layers to produce a unified, strategic impact report.

## 📊 System Architecture Diagram

```mermaid
graph TD
    %% Define Styles
    classDef client fill:#2D3748,stroke:#4A5568,color:#fff,stroke-width:2px;
    classDef api fill:#3182CE,stroke:#2B6CB0,color:#fff,stroke-width:2px;
    classDef ai fill:#805AD5,stroke:#6B46C1,color:#fff,stroke-width:2px;
    classDef data fill:#38A169,stroke:#2F855A,color:#fff,stroke-width:2px;
    classDef engine fill:#DD6B20,stroke:#C05621,color:#fff,stroke-width:2px;
    classDef output fill:#E53E3E,stroke:#C53030,color:#fff,stroke-width:2px;

    %% Mobile Input
    subgraph Mobile_Client [📱 Mobile Application Field Agent]
        A1[📸 Incident Photo]:::client
        A2[📍 GPS Coordinates]:::client
        A3[🎙️ Voice Note <br/> FR / Bambara / Fulfulde]:::client
    end

    %% Backend Entry
    B[⚡ FastAPI Backend / API Gateway]:::api
    
    A1 --> B
    A2 --> B
    A3 --> B

    %% NLP / Vision Processing
    subgraph AI_Processing_Layer [🧠 AI Processing Layer]
        C1[🗣️ ASR / NLP Engine <br/> Audio Translation to Text]:::ai
        C2[👁️ Vision AI Engine <br/> Image Classification & Vectors]:::ai
        C3[🔄 Context Aggregator <br/> Combines Visual + Audio Context]:::ai
    end

    B -->|Audio Stream| C1
    B -->|Image Data| C2
    
    C1 -->|Translated Text Context| C3
    C2 -->|Category, Source Size, Vectors| C3

    %% Geospatial Data
    subgraph Geospatial_Data [🌍 Geospatial Data Sources]
        D1[(🗺️ Global Map Data <br/> Overpass API)]:::data
        D2[(🛰️ Spectral Analysis <br/> Satellite Engine)]:::data
        D3[(⛅ Live Weather API <br/> Open-Meteo)]:::data
    end

    B -->|Lat / Lon| D1
    B -->|Lat / Lon| D2
    B -->|Lat / Lon| D3

    %% Core Engine
    subgraph Impact_Engine [⚙️ Core Impact Logic Engine]
        E1[📏 Dynamic Physics Engine <br/> Slope + Weather + Vectors = Radius]:::engine
        E2[🔍 Spatial Calculator <br/> Cross-reference Radius with Maps/Sat]:::engine
        E3[👥 Vulnerability Scorer <br/> Demographics & Infrastructure Assessment]:::engine
    end

    C3 --> E1
    D2 -.->|Slope/Topography| E1
    D3 -.->|Rain/Wind| E1
    
    E1 -->|Factual & Potential Radii| E2
    D1 -.->|Buildings/POIs| E2
    D2 -.->|Land Use / NDVI| E2
    
    E2 --> E3

    %% Expert Chat & Output
    subgraph Strategic_Output [📈 Decision Support System]
        F1[💬 Expert LLM Advisor <br/> Streaming Strategic Recommendations]:::ai
        F2[📊 Unified Dashboard <br/> Real-time Impact Report]:::output
    end

    E3 -->|Impact Metrics| F2
    E3 -->|Contextual Data| F1
    C3 -->|Audio Context| F1
    
    F1 -.->|Real-time Stream| F2
```

---

## 📝 Component Breakdown & Data Flow

### 1. 📱 Mobile Input Layer
Field agents use the Map Action mobile application to capture the reality on the ground. To ensure maximum accessibility and speed, the app collects three key data points:
*   **Incident Photo**: Visual proof of the disaster (Flood, Pollution, Fire).
*   **GPS Coordinates**: Exact Latitude and Longitude for precise geospatial mapping.
*   **Voice Note**: A critical new feature. Users can describe the situation orally in their native language (**French, Bambara, or Fulfulde**). This bypasses literacy barriers and allows for rapid reporting in high-stress situations.

### 2. 🧠 AI Processing Layer (Multimodal)
Once the payload reaches the **FastAPI Backend**, the data is split into specialized AI pipelines:
*   **ASR/NLP Engine**: Processes the voice note using Automatic Speech Recognition (ASR). It identifies the language (e.g., Bambara), transcribes it, and translates it into a standardized text format (French/English). This text provides crucial *invisible context* (e.g., "The water smells like chemicals" or "People are trapped").
*   **Vision AI Engine**: Analyzes the photo to classify the incident, estimate the physical size of the source, and identify **Spread Vectors** (e.g., wind, water current).
*   **Context Aggregator**: Fuses the translated voice context with the visual data.

### 3. 🌍 Geospatial Data Acquisition
In parallel, the backend fetches real-time environmental data using the GPS coordinates:
*   **Weather Data**: Current wind speed, temperature, and precipitation.
*   **Satellite Data**: Topography (slope), Land Use (Urban/Agricultural), and vegetation indices (NDVI).
*   **Map Data**: OpenStreetMap infrastructure (hospitals, schools, residential buildings).

### 4. ⚙️ Core Impact Logic Engine
This is the heart of the system.
*   **Dynamic Physics Engine**: Instead of drawing a static circle, it calculates a **Factual Radius** and a **Potential Risk Radius** by combining the AI spread vectors (e.g., water) with the environmental physics (e.g., slope and rain).
*   **Spatial Calculator & Vulnerability Scorer**: It filters the map data within these dynamic radii. If map data is missing, it uses satellite Land Use data to perform a **Probabilistic Injection** (estimating population density based on the urban footprint).

### 5. 📈 Decision Support System
*   **Expert LLM Advisor**: A custom fine-tuned Transformer model receives the entire JSON payload (Impact metrics, demographics, weather) PLUS the translated Voice Note context. It streams strategic, actionable recommendations to decision-makers in real-time.
*   **Unified Dashboard**: Displays the quantified impact (Exposed population, threatened infrastructure) alongside the live AI chat, enabling rapid humanitarian logistics deployment.
