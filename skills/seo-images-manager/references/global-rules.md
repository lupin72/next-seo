# Global SEO Rules for Image Optimization

**Version:** 1.0
**Last Updated:** 2026-04-30

These rules apply to ALL client projects unless explicitly overridden in the project's `PROJECT.md` file.

## File Naming Conventions

### Format Rules
- Use lowercase letters only
- Separate words with hyphens (`-`), never underscores or spaces
- Max 5-7 words in file name (excluding extension)
- Prefer `.webp` format for best compression and SEO
- Include target keyword naturally in the file name
- Never use generic names: `IMG_`, `DSC_`, `foto-`, `imagen-`, `photo-`, `image-`

### Structure Pattern
```
[subject]-[qualifier]-[location/brand].webp
```

**Examples:**
- `hotel-swimming-pool-beachfront-peniscola.webp`
- `leather-sofa-modern-living-room.webp`
- `organic-coffee-beans-fair-trade.webp`
- `digital-marketing-strategy-dashboard.webp`

### Industry-Specific Patterns

**Hospitality:**
```
[amenity]-[feature]-[hotel-name]-[location].webp
piscina-toboganes-hotel-acuazul-peniscola.webp
```

**E-commerce:**
```
[product]-[variant]-[brand]-[color/size].webp
leather-jacket-biker-style-zara-black.webp
```

**Real Estate:**
```
[property-type]-[rooms]-[location]-[feature].webp
apartment-3-bedroom-madrid-balcony.webp
```

**Blog/Content:**
```
[topic]-[subtopic]-[year/context].webp
seo-image-optimization-guide-2026.webp
```

## Anti-Cannibalization Rules

### Core Principle
**NEVER repeat the same primary keyword across two file names in the same project.**

### Implementation
- Each image must target a UNIQUE keyword variant
- Use synonyms and long-tail variations to diversify
- Track used keywords across the session to prevent overlap
- If two images show similar subjects, differentiate by angle, detail, or context

### Synonym Strategies by Language

**Spanish (es):**
- "piscina" → "zona de baño", "complejo acuático", "parque acuático"
- "habitación" → "suite", "alojamiento", "apartamento", "room"
- "playa" → "costa", "litoral", "orilla", "arena"
- "niños" → "infantil", "familiar", "peques", "kids"
- "vistas" → "panorámica", "mirador", "skyline"

**English (en):**
- "pool" → "swimming area", "aquatic complex", "water park"
- "room" → "suite", "accommodation", "apartment"
- "beach" → "coast", "shore", "seaside"
- "kids" → "children", "family", "junior"
- "view" → "panorama", "outlook", "vista"

**Italian (it):**
- "piscina" → "zona balneare", "complesso acquatico", "parco acquatico"
- "camera" → "suite", "alloggio", "appartamento"
- "spiaggia" → "costa", "litorale", "riva"
- "bambini" → "infantile", "familiare", "junior"
- "vista" → "panorama", "veduta", "affaccio"

**French (fr):**
- "piscine" → "zone de baignade", "complexe aquatique", "parc aquatique"
- "chambre" → "suite", "logement", "appartement"
- "plage" → "côte", "littoral", "rivage"
- "enfants" → "infantile", "familial", "junior"
- "vue" → "panorama", "point de vue", "perspective"

### Differentiation Examples
When two images show similar content:
- Image 1: `piscina-exterior-adultos-hotel.webp`
- Image 2: `toboganes-parque-acuatico-niños.webp`

## Alt Text Guidelines

### Core Rules
- Max 125 characters
- Must describe what the image SHOWS, not what you want it to rank for
- Include ONE primary keyword naturally
- Do not start with "Image of", "Photo of", "Imagen de", "Foto de"
- Include brand name when natural
- Include location when natural, but not in every single alt text

### Language-Specific Guidelines

**Spanish (es):**
```
Piscina exterior con tumbonas en Hotel Acuazul, primera línea de playa
```

**English (en):**
```
Outdoor pool with sun loungers at Hotel Acuazul, beachfront location
```

**Italian (it):**
```
Piscina esterna con lettini presso Hotel Acuazul, fronte mare
```

**French (fr):**
```
Piscine extérieure avec transats à l'Hôtel Acuazul, en bord de mer
```

### Quality Criteria
✅ **Good:**
- Descriptive and specific
- Natural keyword integration
- Contextual information (location, brand, unique features)

❌ **Bad:**
- Generic descriptions ("Image of pool")
- Keyword stuffing ("hotel pool beach spa kids animation")
- Too short ("pool") or too long (>125 chars)

## Title Attribute Guidelines

- Shorter than alt text (3-8 words)
- Different from alt text (complementary, not duplicate)
- Include brand or location
- Capitalize first letter of each word

**Examples:**
- `Hotel Acuazul Pool Peñiscola`
- `Family Suite Ocean Views`
- `Organic Fair Trade Coffee Beans`

## Caption Guidelines

- User-facing text displayed below the image
- Natural, engaging, informative
- Can include a call to action
- Written in project's primary language

**Examples:**
- **Spanish:** `Disfruta de nuestra piscina exterior con vistas directas a la playa`
- **English:** `Enjoy our outdoor pool with direct beach views`
- **Italian:** `Goditi la nostra piscina esterna con vista diretta sulla spiaggia`

## Description (WordPress Media Library)

- Longer form text (1-2 sentences)
- Include semantic keywords and related terms
- Used internally by WordPress for search and organization
- Rich context for AI-powered media library search

**Example:**
```
Vista de la piscina exterior del Hotel Acuazul con zona de solárium,
tumbonas y sombrillas. El hotel está situado a primera línea de playa
en el paseo marítimo de Peñíscola, Costa Azahar.
```

## Page Context Recommendations

When suggesting page placement, consider:
- Which page of the website will host this image
- What H2/H3 heading should be near the image
- What surrounding paragraph text would maximize SEO relevance
- Whether a schema markup (ImageObject) would be beneficial

## WordPress Implementation

### Upload Checklist
- ✅ Fill all metadata fields: Title, Alt Text, Caption, Description
- ✅ Compress images before upload (target < 100KB for web, < 200KB for hero)
- ✅ Use `.webp` format with `.jpg` fallback
- ✅ Enable lazy loading for images below the fold
- ✅ Implement responsive `srcset` attributes

### SEO Plugin Integration
- Use Rank Math or Yoast to auto-generate image sitemaps
- Ensure images are included in XML sitemap
- Enable Open Graph and Twitter Card image metadata
- Add ImageObject schema where applicable

### Performance Optimization
- Serve images via CDN if available
- Use WebP with JPEG/PNG fallback
- Implement lazy loading for below-the-fold images
- Add `width` and `height` attributes to prevent CLS

## Competitive SEO Strategy

### Research Phase
1. Identify top 3-5 competitors
2. Analyze their image naming patterns
3. Find keyword gaps (keywords they rank for, you don't)
4. Identify unique features to emphasize

### Differentiation Strategy
- Target keywords where competitors rank but you don't
- Emphasize unique features in image names
- Use location proximity keywords when advantageous
- Create image content competitors can't match
- Exploit competitor weaknesses in visual content

### Example: Hotel vs Competitor
**Competitor weakness:** Far from town center, small pool, no water park
**Your strategy:**
- Use keywords: "cerca-centro", "parque-acuatico", "piscina-grande"
- Create images showcasing unique amenities
- Highlight location advantages in alt text

## Override Mechanism

Projects can override these global rules in their `PROJECT.md` file:

### PROJECT.md Override Example
```markdown
## SEO Specifications

### Image SEO Overrides

#### Naming Convention Override
- Max 3-4 words (shorter than global 5-7)
- Always include brand name at end

#### Alt Text Override
- Max 100 characters (shorter than global 125)
- Always include year for blog posts

#### Language-Specific Rules
- Primary: Italian
- Secondary: English
- Tertiary: Spanish
```

## Quality Gates

Before finalizing image metadata, check:

1. **Uniqueness:** No duplicate keywords in same project
2. **Length:** File name 5-7 words, alt text ≤125 chars
3. **Keyword density:** ONE primary keyword per image
4. **Cannibalization:** No >80% similarity to existing images
5. **Format:** Lowercase, hyphens, .webp extension
6. **Completeness:** All fields filled (file name, alt, title, caption, description)

## Versioning

This file may be updated with new industry patterns, language support, or best practices. Projects using older versions will continue to work but may benefit from updating to latest global rules.

**Change Log:**
- v1.0 (2026-04-30): Initial global rules extracted from hotel-image-seo skill
