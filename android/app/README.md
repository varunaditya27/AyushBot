<div align="center">

# 📱 Android App Module

**The Core Application Codebase for the ASHA Tablet Interface**

</div>

## 📌 Overview

The `/android/app` directory contains the actual source code, resources, and manifest for the AyushBot Android application. This is the modular heart of the frontend, separating the Android-specific execution logic from the root Gradle configurations.

## 🏗️ Module Architecture

```mermaid
graph TD
    APP((app/)):::root
    SRC((src/main/)):::src
    TEST((src/test/)):::test
    ANDTEST((src/androidTest/)):::andtest
    
    APP --> SRC
    APP --> TEST
    APP --> ANDTEST
    
    SRC --> JAVA[java/com/ayushbot/app/]
    SRC --> RES[res/]
    SRC --> MANIFEST[AndroidManifest.xml]
    
    JAVA --> UI[ui/]
    JAVA --> DATA[data/]
    JAVA --> NAV[navigation/]
    
    classDef root fill:#e0f7fa,stroke:#006874;
    classDef src fill:#e8f5e9,stroke:#2e7d32;
    classDef test fill:#fff3e0,stroke:#e65100;
    classDef andtest fill:#f3e5f5,stroke:#6a1b9a;
```

## 🧩 Directory Contents

- **`src/main/java/`**: Kotlin source code following MVVM and Clean Architecture.
  - **`ui/`**: Jetpack Compose screens, generic components, and the customized Material 3 Design System.
  - **`data/`**: Room persistent database entities, DAOs, and UI State models.
  - **`navigation/`**: Type-safe Compose Navigation routing logic mapping.
- **`src/main/res/`**: Android external resources.
  - **`values/`**: Global color definitions, font certification arrays for Google Fonts (JetBrains Mono/Noto Sans), and static strings.
  - **`mipmap/`**: Adaptive launcher icons.
- **`build.gradle.kts`**: The module-level build script defining `compileSdk`, Compose dependencies, and ProGuard rules.

## 🛠️ Build Artifacts

When you run `./gradlew assembleDebug` from the parent directory, this module compiles the final APK. All generated UI code and Room SQLite boilerplate is written to `app/build/generated/`, which is strictly ignored via Git.
