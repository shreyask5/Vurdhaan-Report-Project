# Vurdhaan Reports - Frontend

A comprehensive carbon compliance reporting platform for aviation, supporting CORSIA, EU ETS, UK ETS, CH ETS, and ReFuelEU schemes.

## Overview

Vurdhaan Reports is a modern web application that streamlines carbon compliance reporting for the aviation industry. The platform provides automated validation, monitoring plan reviews, and comprehensive reporting capabilities.

## Technologies

This project is built with:

- **Vite** - Fast build tool and development server
- **TypeScript** - Type-safe JavaScript
- **React** - UI framework
- **shadcn-ui** - Component library
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

```sh
# Clone the repository
git clone <YOUR_GIT_URL>

# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will be available at `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run build:dev` - Build in development mode
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/     # Reusable UI components
├── contexts/       # React context providers
├── pages/          # Page components
├── lib/            # Utility functions
└── assets/         # Static assets
```

## Supported Compliance Schemes

- **CORSIA** - Carbon Offsetting and Reduction Scheme for International Aviation
- **EU ETS** - European Union Emissions Trading System
- **UK ETS** - United Kingdom Emissions Trading Scheme
- **CH ETS** - Swiss Emissions Trading System
- **ReFuelEU** - ReFuelEU Aviation Initiative

## Features

- Project management and tracking
- Document upload and validation
- Monitoring plan review
- Real-time collaboration with AI assistance
- Multi-scheme compliance support
- Automated data validation

## Contributing

Please follow the existing code style and ensure all tests pass before submitting pull requests.

## License

Proprietary - All rights reserved
