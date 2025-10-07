# ServicePro - Professional Service Platform (Frontend Only)

## Overview
This is a **frontend-only** demo of a professional service-based product website. All authentication and data management features are simulated using client-side state and localStorage. No real backend is connected.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Project Structure

```
src/
├── components/
│   ├── layout/          # Header, Footer
│   ├── home/            # Homepage sections (Hero, Features, Pricing, etc.)
│   └── ui/              # shadcn/ui components
├── contexts/
│   └── AuthContext.tsx  # Mock authentication (FRONTEND ONLY)
├── pages/
│   ├── Index.tsx        # Homepage
│   ├── Login.tsx        # User login
│   ├── Signup.tsx       # User signup
│   ├── AdminLogin.tsx   # Admin login
│   ├── Dashboard.tsx    # User dashboard
│   └── Admin.tsx        # Admin dashboard
└── assets/              # Images and static files
```

## 🎨 Design System

All styles are defined in the design system using HSL colors and semantic tokens:
- `src/index.css` - CSS custom properties and design tokens
- `tailwind.config.ts` - Tailwind extensions and animations

**Key Features:**
- Professional blue/purple gradient scheme
- Smooth animations and transitions
- Fully responsive design
- Dark mode support (toggle in header)
- Accessible components (WCAG AA)

## 🔐 Mock Authentication

The app includes client-side mock authentication:
- **User Login** (`/login`) - Access user dashboard
- **Admin Login** (`/admin/login`) - Access admin dashboard
- State stored in localStorage for demo purposes

**Important:** This is NOT real authentication. To implement real auth:
1. Replace `AuthContext.tsx` with actual auth provider (Supabase, Auth0, etc.)
2. Remove localStorage mock session
3. Add proper API calls and token management

## 📅 Calendly Integration

Update the Calendly URL in `src/components/home/DemoSection.tsx`:

```typescript
const CALENDLY_URL = 'https://calendly.com/your-handle/demo';
```

Or use environment variables (create `.env` from `.env.example`).

## 📄 Pages & Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Sales/landing page with hero, features, pricing, testimonials |
| `/login` | User Login | Mock user authentication |
| `/signup` | User Signup | Mock user registration |
| `/admin/login` | Admin Login | Mock admin authentication |
| `/dashboard` | User Dashboard | Profile, subscription, billing UI |
| `/admin` | Admin Dashboard | KPIs, user management, content management |

## 🎯 Features

### Homepage Sections
- **Hero** - Compelling value proposition with CTAs
- **Features** - 6-item grid + 3 detailed feature showcases
- **Testimonials** - Customer reviews with ratings
- **Pricing** - 3 tiers with monthly/yearly toggle
- **Demo Booking** - Calendly integration
- **FAQ** - Accordion with common questions

### User Dashboard
- Profile management
- Subscription status
- Billing history (mock data)
- Notification preferences
- Quick actions

### Admin Dashboard
- KPI cards (MRR, users, churn)
- User management table
- Plan analytics
- Content management (mock)

## 🛠 Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **React Router** for routing
- **Zod** for form validation
- **Sonner** for toast notifications

## 🚦 Next Steps (Production Ready)

To make this production-ready:

1. **Add Real Authentication**
   - Integrate Supabase, Auth0, or similar
   - Replace `AuthContext` mock
   - Add secure session management

2. **Connect Backend**
   - Set up API endpoints for user/subscription data
   - Add database for user profiles and subscriptions
   - Implement real payment processing (Stripe, etc.)

3. **Add Analytics**
   - Google Analytics or similar
   - User behavior tracking
   - Conversion tracking

4. **Performance Optimization**
   - Image optimization
   - Code splitting
   - CDN for static assets

5. **SEO Enhancement**
   - Add meta tags
   - Implement structured data
   - Create sitemap

6. **Testing**
   - Unit tests for components
   - Integration tests for flows
   - E2E tests for critical paths

## 📝 Configuration

### Editing Site Content

Most content can be edited in the respective component files:
- Hero text: `src/components/home/HeroSection.tsx`
- Features: `src/components/home/FeaturesSection.tsx`
- Pricing plans: `src/components/home/PricingSection.tsx`
- Testimonials: `src/components/home/TestimonialsSection.tsx`
- FAQs: `src/components/home/FAQSection.tsx`

### Styling

All colors and design tokens are in:
- `src/index.css` - CSS variables
- `tailwind.config.ts` - Tailwind configuration

## 📧 Support

For questions or issues, refer to the component comments marked with:
```typescript
// FRONTEND ONLY: [explanation of what needs to be replaced]
```

## 📜 License

This is a demo project. Replace with your license as needed.
