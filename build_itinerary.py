#!/usr/bin/env python3
"""
build_itinerary.py
Parses source_itinerary.csv, merges Allan Su's Guidebook knowledge,
adds curated location-tailored recommendations, and outputs master_itinerary.json.
"""

import csv
import json
import re
from datetime import datetime

# Curated location-tailored recommendations by Day & City
TAILORED_RECOMMENDATIONS = {
    1: { # Nov 10 - Osaka
        "neighborhood": "Shinsaibashi & Dotonbori",
        "highlights": [
            {
                "title": "Hozenji Yokocho & Mossy Fudo Myoo",
                "category": "Atmosphere & Culture",
                "description": "Just off Dotonbori, slip into this quiet stone-paved alley. Splash water on the moss-covered Mizukake Fudo statue for good luck and take atmospheric lantern photos at dusk.",
                "maps_query": "Hozenji Yokocho, Osaka"
            },
            {
                "title": "Rikuro Ojisan Fluffy Cheesecake",
                "category": "Must-Eat Treat",
                "description": "Near Namba Station. Watch the bell ring every time a freshly baked, ultra-fluffy soufflé cheesecake comes out of the oven. Eat warm or save for your hotel room.",
                "maps_query": "Rikuro Ojisan Namba, Osaka"
            },
            {
                "title": "Kushikatsu Yaekatsu (Shinsekai)",
                "category": "Food Specialty",
                "description": "The quintessential Osaka street snack in the shadow of Tsutenkaku Tower. Crispy skewered pork, lotus root, and quail eggs. Note: Strict no double-dipping rule in the shared sauce!",
                "maps_query": "Yaekatsu Shinsekai, Osaka"
            }
        ]
    },
    2: { # Nov 11 - Osaka
        "neighborhood": "Osaka Castle, Amerikamura & Umeda",
        "highlights": [
            {
                "title": "Kogaryu Takoyaki in Triangle Park",
                "category": "Youth Culture Snack",
                "description": "Award-winning takoyaki topped with spicy mayonnaise and scallions in Amerikamura. Grab a boat and sit on the benches in Sankaku Koen (Triangle Park) like local Osaka youths.",
                "maps_query": "Kogaryu Amerikamura, Osaka"
            },
            {
                "title": "Sunset Timing at Umeda Sky Building",
                "category": "Pro-Tip / Sunset",
                "description": "Arrive at the Floating Garden Observatory 45 minutes before sunset. You get the 360-degree daylight view over Osaka Bay, the golden hour transition, and the glowing luminescent floor at night.",
                "maps_query": "Umeda Sky Building, Osaka"
            },
            {
                "title": "Hanshin Department Store B1 Snack Park",
                "category": "Food Hall",
                "description": "Famous standing food court under Umeda. Try authentic Osaka Ikayaki (chewy pressed squid crepe/pancake) for under ¥250.",
                "maps_query": "Hanshin Snack Park Umeda, Osaka"
            }
        ]
    },
    3: { # Nov 12 - Koyasan
        "neighborhood": "Mount Koya (Wakayama)",
        "highlights": [
            {
                "title": "Okunoin Lantern Cemetery Night Walk",
                "category": "Spiritual Experience",
                "description": "Walk the 2km path through 200,000 ancient stone memorials and towering cedar trees under stone lanterns after dark. Atmospheric, serene, and mystical.",
                "maps_query": "Okunoin Cemetery, Koyasan"
            },
            {
                "title": "Kadohama Goma-dofu (Sesame Tofu)",
                "category": "Buddhist Delicacy",
                "description": "1,200-year-old Koyasan specialty made from ground sesame seeds, mountain spring water, and arrowroot. Silky texture, eaten with freshly grated wasabi and dashi soy sauce.",
                "maps_query": "Kadohama Goma-dofu Koyasan"
            },
            {
                "title": "Torodo (Hall of 10,000 Lanterns)",
                "category": "Sacred Site",
                "description": "Located directly behind Kobo Daishi's mausoleum. Contains over 10,000 lanterns with two eternal flames said to have burned continuously for over 1,000 years.",
                "maps_query": "Torodo Hall of Lanterns Koyasan"
            }
        ]
    },
    4: { # Nov 13 - Nara
        "neighborhood": "Nara Park & Naramachi",
        "highlights": [
            {
                "title": "Todai-ji Nigatsu-do Veranda",
                "category": "Hidden Viewpoint",
                "description": "Climb up the wooden stairs behind the Great Buddha hall to Nigatsu-do. The elevated wooden balcony offers a free, panoramic view over the entire Nara basin with almost no crowds.",
                "maps_query": "Nigatsudo Todaiji Nara"
            },
            {
                "title": "Nakatanidou Freshly Pounded Mochi Timing",
                "category": "Show & Snack",
                "description": "High-speed mochitsuki hammering happens every 30-40 minutes outside the shop. Eat the warm yomogi (mugwort) mochi immediately while the dough is ultra-soft.",
                "maps_query": "Nakatanidou Nara"
            },
            {
                "title": "Kakinoha-zushi at Hiraso",
                "category": "Local Specialty",
                "description": "Nara's historic sushi pressed and wrapped in persimmon leaves (which naturally preserves the mackerel and salmon). Perfect for a light lunch or to take on the train.",
                "maps_query": "Hiraso Nara Kakinohazushi"
            }
        ]
    },
    5: { # Nov 14 - Kyoto
        "neighborhood": "Gion & Southern Higashiyama",
        "highlights": [
            {
                "title": "Kiyomizu-dera Autumn Night Light-Up",
                "category": "Seasonal Must-See",
                "description": "Mid-November features the special evening illumination. The wooden stage and red maple trees are lit against the dark sky, with a blue searchlight beam pointing toward Kyoto city.",
                "maps_query": "Kiyomizu-dera Kyoto"
            },
            {
                "title": "Shirakawa Canal Walk",
                "category": "Atmosphere",
                "description": "Walk along the Shirakawa River near Tatsumi Bridge at dusk. Far quieter and more romantic than Hanami-koji, with weeping willows and wooden teahouse reflections in the water.",
                "maps_query": "Shirakawa Canal Gion Kyoto"
            },
            {
                "title": "% Arabica Kyoto Higashiyama",
                "category": "Artisan Coffee",
                "description": "World-class espresso bar situated right on the cobbled hill facing Yasaka Pagoda (Hokan-ji). Perfect photo spot with Kyoto's most iconic silhouette.",
                "maps_query": "Arabica Kyoto Higashiyama"
            }
        ]
    },
    6: { # Nov 15 - Kyoto
        "neighborhood": "Arashiyama & Northern Kyoto",
        "highlights": [
            {
                "title": "Beat the Crowds at Bamboo Grove (Early Morning)",
                "category": "Timing Hack",
                "description": "Tour groups arrive at Arashiyama by 8:30 AM. Arrive between 6:30 AM - 7:30 AM to have the majestic bamboo grove entirely to yourself for serene photographs.",
                "maps_query": "Arashiyama Bamboo Grove Kyoto"
            },
            {
                "title": "Gio-ji Temple Moss Garden",
                "category": "Hidden Gem",
                "description": "A 15-minute walk past the main Arashiyama path. A tranquil thatched-roof hermitage surrounded by a lush carpet of moss, covered in fallen vibrant red maple leaves in mid-November.",
                "maps_query": "Gio-ji Temple Kyoto"
            },
            {
                "title": "Golden Pavilion Reflection at Kinkaku-ji",
                "category": "Photo Tip",
                "description": "Best visited in the early afternoon when the sun directly hits the top floors, casting a mirror-like gold reflection onto Kyoko-chi (Mirror Pond).",
                "maps_query": "Kinkaku-ji Kyoto"
            }
        ]
    },
    7: { # Nov 16 - Kyoto
        "neighborhood": "Fushimi Inari, Nanzen-ji & Pontocho",
        "highlights": [
            {
                "title": "Suirokaku Roman Aqueduct at Nanzen-ji",
                "category": "Architecture Gem",
                "description": "Hidden behind Nanzen-ji's main hall is a 19th-century red-brick Roman-style aqueduct. The contrast between ancient Japanese temple gardens and Western arched brick is stunning.",
                "maps_query": "Suirokaku Nanzen-ji Kyoto"
            },
            {
                "title": "Blue Bottle Coffee Kyoto Machiya",
                "category": "Unique Cafe",
                "description": "A 100-year-old traditional two-story machiya townhouse converted into a serene, minimalist roastery just 3 minutes from Nanzen-ji.",
                "maps_query": "Blue Bottle Coffee Kyoto Cafe"
            },
            {
                "title": "Fushimi Inari Yotsutsuji Viewpoint",
                "category": "Hike Tip",
                "description": "90% of tourists stop at the lower torii loops. Keep ascending for 30 minutes to Yotsutsuji intersection for a soft drink, bench rest, and panoramic Kyoto skyline views.",
                "maps_query": "Fushimi Inari Yotsutsuji Kyoto"
            }
        ]
    },
    8: { # Nov 17 - Kanazawa
        "neighborhood": "Omicho & Hirosaka",
        "highlights": [
            {
                "title": "Nodoguro (Blackthroat Seaperch) Kaisen-don",
                "category": "Seafood Crown Jewel",
                "description": "Kanazawa's most famous seasonal fish. At Omicho Market, get a kaisen-don (seafood bowl) with flame-seared fatty nodoguro seasoned with sea salt.",
                "maps_query": "Omicho Market Kanazawa"
            },
            {
                "title": "D.T. Suzuki Museum Water Mirror Garden",
                "category": "Zen Architecture",
                "description": "Designed by Yoshio Taniguchi. Sit quietly in the Contemplative Space Pavilion and gaze at the still water pool where periodic ripples break the stone reflections.",
                "maps_query": "D.T. Suzuki Museum Kanazawa"
            },
            {
                "title": "The Swimming Pool by Leandro Erlich",
                "category": "Museum Booking Tip",
                "description": "Inside the 21st Century Museum. Looking down from above is free, but stepping underground inside the pool requires a timed reservation ticket booked online on the museum website.",
                "maps_query": "21st Century Museum of Contemporary Art Kanazawa"
            }
        ]
    },
    9: { # Nov 18 - Kanazawa
        "neighborhood": "Kenroku-en, Castle & Higashi Chaya",
        "highlights": [
            {
                "title": "Kenrokuen Yukitsuri (Snow Ropes)",
                "category": "Autumn/Winter Icon",
                "description": "Mid-November is when gardeners raise the traditional conical rope arrays protecting centuries-old Karasaki pine branches from heavy snowfall. An iconic Japanese landscape.",
                "maps_query": "Kenroku-en Kanazawa"
            },
            {
                "title": "Hakuichi Edible 24K Gold Leaf Soft Cream",
                "category": "Iconic Treat",
                "description": "Right outside Kenrokuen or in Higashi Chaya. A full sheet of pure 24-karat gold leaf draped delicately over rich Hokkaido vanilla soft serve.",
                "maps_query": "Hakuichi Kenrokuen Kanazawa"
            },
            {
                "title": "Kanazawa Oden at Akatama or Miyoshi",
                "category": "Warm Comfort Dinner",
                "description": "Kanazawa consumes more oden than any other city in Japan. Warm up with baigai (sea snail), kuruma-fu (wheel-shaped wheat gluten), and soft daikon in clear golden dashi.",
                "maps_query": "Akatama Honten Kanazawa"
            }
        ]
    },
    10: { # Nov 19 - Takayama
        "neighborhood": "Sanmachi-suji Old Town & Okuhida",
        "highlights": [
            {
                "title": "Kotteushi Grade A5 Hida Beef Nigiri",
                "category": "Street Food Star",
                "description": "In Sanmachi-suji old town. Two pieces of melt-in-your-mouth blowtorched Hida wagyu sushi served on a crisp edible shrimp rice cracker so there's zero waste.",
                "maps_query": "Kotteushi Takayama"
            },
            {
                "title": "Self-Serve Sake Tasting at Harada Brewery",
                "category": "Sake Experience",
                "description": "Purchase a souvenir ceramic ochoko cup for ~¥400, then sample over 10 varieties of freshly pressed local mountain sake directly from the tap.",
                "maps_query": "Harada Sake Brewery Takayama"
            },
            {
                "title": "Mitarashi Dango with Savory Soy Sauce",
                "category": "Traditional Snack",
                "description": "Unlike Tokyo's sweet glaze, Takayama dango is grilled over charcoal with savory, unsweetened soy sauce until slightly charred and fragrant.",
                "maps_query": "Fujiya Dango Takayama"
            }
        ]
    },
    11: { # Nov 20 - Takayama & Tokyo
        "neighborhood": "Okuhida Alps & Ikebukuro",
        "highlights": [
            {
                "title": "Shinhotaka Double-Decker Ropeway",
                "category": "Mountain Panorama",
                "description": "Japan's only two-story cable car. Ascends through the clouds to the 2,156m rooftop observation deck of Mt. Hotaka with breathtaking views of the Northern Alps snowcaps.",
                "maps_query": "Shinhotaka Ropeway Takayama"
            },
            {
                "title": "Mutekiya Ramen (Ikebukuro)",
                "category": "Late Night Dinner",
                "description": "Steps from your hotel (Hotel Metropolitan Ikebukuro). Famous for thick pork bone broth, giant melt-in-mouth chashu, and custom seaweed printed with multilingual greetings.",
                "maps_query": "Mutekiya Ikebukuro Tokyo"
            }
        ]
    },
    12: { # Nov 21 - Tokyo
        "neighborhood": "Shibuya & Harajuku",
        "highlights": [
            {
                "title": "Shibuya Sky Sunset Ticket Strategy",
                "category": "Booking Alert",
                "description": "Tickets for the sunset window sell out within 15 minutes when released 4 weeks ahead. Book online at midnight JST 28 days prior for the ultimate rooftop view.",
                "maps_query": "Shibuya Sky Tokyo"
            },
            {
                "title": "Cat Street Harajuku Backstreets",
                "category": "Hidden Shopping",
                "description": "Skip the chaotic Takeshita Street after a quick peek and stroll Cat Street towards Shibuya. Trendy Japanese designer stores, quiet artisan cafes, and vintage denim.",
                "maps_query": "Cat Street Shibuya Tokyo"
            },
            {
                "title": "Nonbei Yokocho (Drinker's Alley)",
                "category": "Retro Nightlife",
                "description": "Directly next to Shibuya Station under the train tracks. Lantern-lit post-war corridor packed with tiny 5-seat izakayas oozing Showa-era charm.",
                "maps_query": "Nonbei Yokocho Shibuya Tokyo"
            }
        ]
    },
    13: { # Nov 22 - Tokyo
        "neighborhood": "Toyosu & Shinjuku",
        "highlights": [
            {
                "title": "teamLab Planets Attire Warning",
                "category": "Visitor Tip",
                "description": "You walk barefoot through knee-deep water installations and over mirrored glass floors. Wear pants that easily roll above the knees and avoid skirts/dresses.",
                "maps_query": "teamLab Planets Tokyo Toyosu"
            },
            {
                "title": "Tokyo Metropolitan Gov Building Observatory",
                "category": "Free View",
                "description": "If you want a breathtaking 45th-floor view of Tokyo and Mt. Fuji for completely FREE, head to the Tocho Twin Towers in West Shinjuku.",
                "maps_query": "Tokyo Metropolitan Government Building Shinjuku"
            },
            {
                "title": "Golden Gai 6-Seat Micro Bars",
                "category": "Bar Hopping",
                "description": "A maze of six narrow alleys packed with 200 tiny bars. Look for bars with English signs indicating 'No Cover Charge' (e.g., Bar Albatross or Champion) for a welcoming drink.",
                "maps_query": "Shinjuku Golden Gai Tokyo"
            }
        ]
    },
    14: { # Nov 23 - Tokyo
        "neighborhood": "Asakusa, Akihabara & Minato",
        "highlights": [
            {
                "title": "Early Morning Senso-ji Atmosphere",
                "category": "Photo Hack",
                "description": "Visit Senso-ji around 7:00-7:30 AM before the Nakamise vendor shutters open. You can photograph the iconic giant Kaminarimon lantern with zero crowds.",
                "maps_query": "Senso-ji Asakusa Tokyo"
            },
            {
                "title": "Super Potato Retro Gaming (Akihabara)",
                "category": "Pop Culture Nostalgia",
                "description": "Floors 3-5 contain vintage Famicom, Game Boy, Neo Geo games, and an old-school 5th floor arcade with arcade cabinets and retro Japanese candy.",
                "maps_query": "Super Potato Akihabara Tokyo"
            },
            {
                "title": "Zojoji Temple with Tokyo Tower Backdrop",
                "category": "Classic Photo Spot",
                "description": "Right in front of Tokyo Tower. Photograph the 600-year-old Buddhist main hall with the illuminated orange Eiffel-style Tokyo Tower rising directly behind it.",
                "maps_query": "Zojoji Temple Tokyo"
            }
        ]
    },
    15: { # Nov 24 - Departure
        "neighborhood": "Tokyo Station & Haneda Airport",
        "highlights": [
            {
                "title": "Daimaru Tokyo B1 Depachika Gift Hall",
                "category": "Gourmet Souvenirs",
                "description": "Before heading to Haneda, stop at Daimaru adjacent to Tokyo Station. Premium boxes of Press Butter Sand, Tokyo Banana, Nenrinya Baumkuchen, and kitkats.",
                "maps_query": "Daimaru Tokyo Department Store"
            },
            {
                "title": "Haneda T3 Edo Ko-ji & Observation Deck",
                "category": "Airport Experience",
                "description": "Terminal 3 features a full reconstructed Edo-period wooden shopping street and a breezy outdoor observation deck watching long-haul widebodies depart against Tokyo Bay.",
                "maps_query": "Haneda Airport Terminal 3 Edo Koji"
            }
        ]
    }
}

# Allan Su Guidebook details database mapped by normalized spot name
GUIDEBOOK_DATA = {
    "dotonbori": {
        "tagline": "The heart of Osaka",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Short 5-minute walk from JR Namba Station or Midosuji Line Shinsaibashi Station via Shinsaibashi-suji.",
        "things_to_do": [
            "Compulsory photo snap with the Glico Running Man sign",
            "Grab takoyaki street snack",
            "Tonbori River 20-minute canal cruise",
            "Stroll through the narrow atmospheric alleys of Hozenji Yokocho"
        ],
        "travel_tips": "Best experienced after sunset when neon billboards and glowing canal lights turn on."
    },
    "shinsaibashi shopping street": {
        "tagline": "Iconic shopping arcade",
        "hours": "11:00 AM - 9:00 PM",
        "price_jpy": "Free",
        "how_to_access": "Directly accessible from Shinsaibashi Subway Station (Midosuji Line).",
        "things_to_do": [
            "Walk the 600-meter covered arcade lined with hundreds of fashion boutiques",
            "Browse souvenirs, electronics, cosmetics, and confectionery",
            "Explore adjoining cafes and nightlife venues"
        ]
    },
    "kuromon market": {
        "tagline": "Osaka's Kitchen",
        "hours": "9:00 AM - 6:00 PM",
        "price_jpy": "Free entry / Pay per stall",
        "how_to_access": "2-minute walk from Nippombashi Station (Sennichimae / Sakaisuji Lines).",
        "things_to_do": [
            "Sample fresh seafood skewers (grilled scallops, crab legs, uni)",
            "Taste freshly prepared Kobe beef skewers and tamagoyaki",
            "Pick up seasonal Japanese fruits (white strawberries, melon)"
        ],
        "travel_tips": "Bring cash as many traditional street food stalls do not take credit cards."
    },
    "shinsekai": {
        "tagline": "Retro 1912 New World district",
        "hours": "Open 24 hours (Shops ~11:00 AM - 10:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "Short walk from Shin-Imamiya Station (JR Osaka Loop) or Dobutsuen-mae Station (Midosuji Line).",
        "things_to_do": [
            "View Tsutenkaku Tower (103m landmark)",
            "Eat famous Osaka Kushikatsu (deep fried skewers) at Daruma or Yaekatsu",
            "Experience the post-WWII retro Showa atmosphere and neon signs"
        ]
    },
    "namba yasaka shrine": {
        "tagline": "Giant lion-head stage",
        "hours": "6:30 AM - 5:00 PM",
        "price_jpy": "Free",
        "how_to_access": "6-minute walk from Namba Station (Midosuji / Nankai lines).",
        "things_to_do": [
            "Marvel at the 12-meter tall, 11-meter wide lion head stage (Ema-den)",
            "Offer a prayer for good fortune and victory over evil spirits",
            "Admire the lion's mouth designed to swallow bad spirits"
        ]
    },
    "osaka castle": {
        "tagline": "Historic Toyotomi fortress",
        "hours": "9:00 AM - 5:30 PM (Last entry 5:00 PM)",
        "price_jpy": "¥600 (Grounds free)",
        "how_to_access": "10-minute walk from Osakajokoen Station (JR Loop Line) or Tanimachi 4-chome Station.",
        "things_to_do": [
            "Climb to the 8th-floor observation deck for panoramic park views",
            "Explore the 8-story museum detailing Toyotomi Hideyoshi's unification of Japan",
            "Walk around the massive outer stone walls, moats, and Nishinomaru Garden"
        ]
    },
    "america-mura": {
        "tagline": "Epicenter of youth fashion",
        "hours": "Open 24 hours (Shops 11:00 AM - 8:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "5-minute walk west of Shinsaibashi Station.",
        "things_to_do": [
            "Shop vintage clothing, streetwear, and quirky vinyl records",
            "People-watch and eat takoyaki at Triangle Park (Sankaku Koen)",
            "Spot colorful urban street art, graffiti, and miniature Statue of Liberty"
        ]
    },
    "umeda sky building": {
        "tagline": "Floating Garden Observatory",
        "hours": "9:30 AM - 10:30 PM (Last entry 10:00 PM)",
        "price_jpy": "¥2,000",
        "how_to_access": "10-15 minute walk from JR Osaka Station or Umeda Subway Station.",
        "things_to_do": [
            "Ride the glass-encased escalator suspended between the two towers",
            "Step onto the open-air circular roof deck on the 39th floor",
            "Walk the Lumi Sky Walk path which glows in the dark at night"
        ]
    },
    "don quijote": {
        "tagline": "Souvenir mega-store & Ebisu Ferris wheel",
        "hours": "Open 24 hours (Ferris wheel 11:00 AM - 11:00 PM)",
        "price_jpy": "¥600 for Ferris wheel",
        "how_to_access": "Located right on Dotonbori canal, next to Tazaemon Bridge.",
        "things_to_do": [
            "Ride the 77-meter yellow oval Ebisu Ferris wheel overlooking Dotonbori",
            "Shop multiple floors of Japanese snacks, cosmetics, matchas, and duty-free goods"
        ]
    },
    "danjo garan complex": {
        "tagline": "Sacred center of Shingon Buddhism",
        "hours": "8:30 AM - 5:00 PM",
        "price_jpy": "¥500 (Grounds free)",
        "how_to_access": "10-minute bus from Koyasan Cable Car station (Senjuinbashi stop).",
        "things_to_do": [
            "Admire the vibrant vermilion Konpon Daito Pagoda (48.5m high)",
            "View Miedo Hall housing sacred statues of Kobo Daishi",
            "Walk through Kondo (Golden Hall), site of major temple rituals"
        ]
    },
    "daimon gate": {
        "tagline": "The monumental South Gate of Koyasan",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Bus stop Daimon Gate on the Koyasan bus loop.",
        "things_to_do": [
            "Inspect the two 12th-century fierce Kongorikishi (Nio) guardian statues",
            "Catch views of the surrounding Kii mountain valley from the edge"
        ]
    },
    "reihokan museum": {
        "tagline": "Treasures of Mount Koya",
        "hours": "8:30 AM - 5:30 PM",
        "price_jpy": "¥600",
        "how_to_access": "Located adjacent to Danjo Garan complex.",
        "things_to_do": [
            "View over 3,000 artifacts including National Treasures, sacred mandalas, and Buddhist sculptures"
        ]
    },
    "kongobu-ji": {
        "tagline": "Head monastery of Mount Koya",
        "hours": "8:30 AM - 5:00 PM",
        "price_jpy": "¥500",
        "how_to_access": "5-minute walk from Senjuinbashi bus stop.",
        "things_to_do": [
            "Marvel at Banryutei Rock Garden (Japan's largest rock garden, representing two dragons emerging from clouds)",
            "Admire the sliding screen paintings (fusuma-e) by Kano School masters in the Ohiroma hall"
        ]
    },
    "okunoin cemetery": {
        "tagline": "Most sacred sanctuary in Koyasan",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Take bus to Ichinohashi or Okunoin-mae stop.",
        "things_to_do": [
            "Walk the 2km path lined with 200,000 mossy tombs under ancient giant cedars",
            "Cross Gobyo-bashi bridge into Kobo Daishi's sacred mausoleum area",
            "Experience the glowing Torodo (Hall of 10,000 Lanterns)"
        ]
    },
    "nakatanidou": {
        "tagline": "Legendary mochi pounding show",
        "hours": "10:00 AM - 7:00 PM",
        "price_jpy": "¥180 - ¥450",
        "how_to_access": "5-minute walk from Kintetsu Nara Station along Sanjo-dori.",
        "things_to_do": [
            "Watch the lightning-fast wooden mallet mochi pounding (mochitsuki)",
            "Eat fresh warm Yomogi (mugwort) mochi filled with sweet azuki bean paste"
        ]
    },
    "nara park": {
        "tagline": "Home to 1,000+ friendly sacred deer",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "5-minute walk from Kintetsu Nara Station or Yellow Bus #2 from JR Nara.",
        "things_to_do": [
            "Buy Shika-senbei (deer crackers, ¥200) and watch the deer bow for food",
            "Walk shaded trails surrounded by historic woods and ponds"
        ]
    },
    "isui-en garden": {
        "tagline": "Edo-period borrowed scenery garden",
        "hours": "9:30 AM - 4:30 PM",
        "price_jpy": "¥1,200",
        "how_to_access": "15-minute walk from Kintetsu Nara Station, near Todai-ji.",
        "things_to_do": [
            "Admire Shakkei ('borrowed scenery') incorporating Mt. Wakakusa and Todai-ji roofline",
            "Walk stone stepping bridges over the reflecting pond",
            "Explore Neiraku Museum of ancient bronze and ceramics"
        ]
    },
    "todai-ji": {
        "tagline": "Daibutsuden - Great Bronze Buddha",
        "hours": "7:30 AM - 5:30 PM",
        "price_jpy": "¥800",
        "how_to_access": "20-minute walk from Kintetsu Nara or bus to Todaiji Daibutsuden stop.",
        "things_to_do": [
            "Enter the world's largest wooden building housing the 15-meter bronze Daibutsu",
            "See the wooden pillar with a hole the same size as Buddha's nostril",
            "Climb up the stone steps to the quiet Nigatsu-do veranda"
        ]
    },
    "katsuga taisha": {
        "tagline": "Shrine of 3,000 Bronze & Stone Lanterns",
        "hours": "6:00 AM - 6:00 PM",
        "price_jpy": "¥500 for inner sanctuary (Grounds free)",
        "how_to_access": "25-minute walk through Nara Park woods from Kintetsu Nara.",
        "things_to_do": [
            "Wander through mossy forest lined with thousands of stone lanterns",
            "Inspect glowing hanging bronze lanterns inside the inner sanctuary"
        ]
    },
    "gion": {
        "tagline": "Historic Geisha & Entertainment district",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "5-minute walk from Gion-Shijo Station (Keihan Line).",
        "things_to_do": [
            "Stroll stone-paved Hanami-koji lined with preserved wooden machiya",
            "Spot Geiko and Maiko heading to evening appointments at dusk",
            "Visit Gion Corner for cultural dance and arts performances"
        ]
    },
    "yasaka shrine": {
        "tagline": "Gion's guardian shrine",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "At the eastern terminus of Shijo-dori in Gion.",
        "things_to_do": [
            "View the dance stage hung with hundreds of glowing paper lanterns at night",
            "Walk through into neighboring Maruyama Park"
        ]
    },
    "ninenzaka & sannenzaka": {
        "tagline": "Preserved stone-paved merchant streets",
        "hours": "Open 24 hours (Shops 10:00 AM - 6:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "Pedestrian paths leading directly up to Kiyomizu-dera.",
        "things_to_do": [
            "Walk preserved Edo-era cobbled alleys with classic tiled roofs",
            "Browse pottery, incense, green tea sweets, and artisan crafts",
            "Photograph Yasaka Pagoda (Hokan-ji) from the slope"
        ]
    },
    "kiyomizu-dera": {
        "tagline": "Temple of pure water & historic wooden stage",
        "hours": "6:00 AM - 6:00 PM (Autumn light-up open until 9:30 PM)",
        "price_jpy": "¥500",
        "how_to_access": "10-minute walk up Matsubara-dori from Kiyomizu-michi bus stop.",
        "things_to_do": [
            "Stand on the legendary wooden stage constructed entirely without nails",
            "Drink from the Otowa Waterfall streams (health, longevity, wisdom)",
            "Visit Jishu Shrine (shrine of love and matchmaking)"
        ]
    },
    "arashiyama bamboo forest": {
        "tagline": "Towering natural green bamboo canopy",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "10-minute walk from JR Saga-Arashiyama or Randen Arashiyama Station.",
        "things_to_do": [
            "Listen to the rustle of 30-meter bamboo canes in the morning breeze",
            "Visit Nonomiya Shrine nestled inside the bamboo groves"
        ]
    },
    "tenryu-ji": {
        "tagline": "UNESCO World Heritage Zen Temple & Garden",
        "hours": "8:30 AM - 5:00 PM",
        "price_jpy": "¥500 (Garden) / +¥300 for main halls",
        "how_to_access": "Directly adjacent to Arashiyama Bamboo Grove entrance.",
        "things_to_do": [
            "Sit before the 14th-century Sogenchi garden pond framed by Arashiyama mountains",
            "View the Cloud Dragon painting on the Hatto hall ceiling"
        ]
    },
    "iwatayama monkey park": {
        "tagline": "Wild Japanese macaques with panoramic Kyoto view",
        "hours": "9:00 AM - 4:00 PM",
        "price_jpy": "¥800",
        "how_to_access": "5-minute walk from Togetsukyo Bridge, followed by a 20-minute uphill hike.",
        "things_to_do": [
            "Feed wild snow monkeys fruit inside the enclosed observation hut",
            "Enjoy wide panoramic views across the Kyoto basin and Hozu River"
        ]
    },
    "kinkaku-ji": {
        "tagline": "The iconic Golden Pavilion",
        "hours": "9:00 AM - 5:00 PM",
        "price_jpy": "¥500",
        "how_to_access": "Direct bus 205 from Kyoto Station to Kinkakuji-michi stop.",
        "things_to_do": [
            "Photograph the top two floors gilded in pure gold leaf reflecting in the pond",
            "Walk the stone garden path and visit Sekkatei teahouse"
        ]
    },
    "fushimi-inari": {
        "tagline": "10,000 Vermilion Torii Gates up Mount Inari",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Directly in front of JR Inari Station (Nara Line, 5m from Kyoto Stn).",
        "things_to_do": [
            "Walk the Senbon Torii tunnel of vermilion gates donated by worshippers",
            "Spot hundreds of sacred stone fox statues holding keys and jewels",
            "Hike up to Yotsutsuji intersection for summit sunset views"
        ]
    },
    "nanzen-ji temple": {
        "tagline": "Sprawling Zen complex & Roman Aqueduct",
        "hours": "8:30 AM - 5:00 PM",
        "price_jpy": "¥600 for Hojo Garden / Sanmon Gate (Grounds free)",
        "how_to_access": "10-minute walk from Keage Station (Tozai Subway Line).",
        "things_to_do": [
            "Climb to the second floor of the monumental Sanmon Gate",
            "Photograph Suirokaku, the 1890 red-brick Roman aqueduct",
            "Relax at the Hojo dry landscape rock garden"
        ]
    },
    "philosophers path": {
        "tagline": "Tetsugaku no Michi stone canal path",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Runs ~2km between Ginkaku-ji and Nanzen-ji.",
        "things_to_do": [
            "Walk alongside the peaceful canal shaded by cherry and maple trees",
            "Stop by artisan ceramics and local tea shops along the route"
        ]
    },
    "honen-in": {
        "tagline": "Secluded temple with thatched gate and moss garden",
        "hours": "6:00 AM - 4:00 PM",
        "price_jpy": "Free (Halls ¥500-800 when open)",
        "how_to_access": "5-minute stroll up the slope from Philosopher's Path.",
        "things_to_do": [
            "Pass through the moss-covered thatched Sanmon Gate",
            "See the two raised white sand mounds (Byakusadan) purifying visitors",
            "Enjoy tranquil koi pond and mossy forest stone bridges"
        ]
    },
    "omicho market": {
        "tagline": "Kanazawa's lively seafood kitchen",
        "hours": "9:00 AM - 5:00 PM",
        "price_jpy": "Free",
        "how_to_access": "15-minute walk from JR Kanazawa Station or 5m on loop bus.",
        "things_to_do": [
            "Feast on fresh Sea of Japan crab, sea urchin, and sweet shrimp",
            "Eat at conveyor sushi joints (Mori Mori Sushi) or Kaisen-don stalls"
        ]
    },
    "d.t. suzuki museum": {
        "tagline": "Minimalist Zen philosophy museum",
        "hours": "9:30 AM - 5:00 PM",
        "price_jpy": "¥310",
        "how_to_access": "10-minute bus from Kanazawa Station to Hondamachi stop.",
        "things_to_do": [
            "Contemplate Zen teachings in the minimalist glass and stone pavilion",
            "Meditate beside the tranquil Water Mirror Garden"
        ]
    },
    "21st century of contemporary art museum": {
        "tagline": "Modern circular art landmark by SANAA",
        "hours": "10:00 AM - 6:00 PM (Public spaces until 10:00 PM)",
        "price_jpy": "¥1,100 - ¥1,400 (Outer circle free)",
        "how_to_access": "Short walk from Kenrokuen Garden or bus to Hirosaka stop.",
        "things_to_do": [
            "Experience Leandro Erlich's 'The Swimming Pool' illusion",
            "Stroll through circular glass galleries open to natural sunlight"
        ]
    },
    "kenrouken garden": {
        "tagline": "One of Japan's Three Great Gardens",
        "hours": "8:00 AM - 5:00 PM (Autumn light-up evenings 5:30-9:00 PM)",
        "price_jpy": "¥320",
        "how_to_access": "Just across the pedestrian bridge from Kanazawa Castle.",
        "things_to_do": [
            "Photograph Kotoji-toro two-legged stone lantern at Kasumigaike Pond",
            "See the ancient Karasaki Pines supported by Yukitsuri snow ropes",
            "Sip matcha at the historic Yugao-tei teahouse"
        ]
    },
    "kanazawa castle": {
        "tagline": "Maeda clan feudal fortress",
        "hours": "8:00 AM - 5:00 PM",
        "price_jpy": "Free grounds (Turrets ¥320)",
        "how_to_access": "Next to Kenrokuen Garden.",
        "things_to_do": [
            "Explore the massive reconstructed Gojukken Nagaya wooden storehouse",
            "Inspect the Hashizume-mon Tsuzuki Yagura defensive watchtower",
            "Admire the white lead-glazed roof tiles and Ishikawa Gate"
        ]
    },
    "higashi-chaya": {
        "tagline": "Preserved historic geisha teahouse district",
        "hours": "Open 24 hours (Shops 10:00 AM - 6:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "10-minute bus from Kanazawa Station to Hashiba-cho stop.",
        "things_to_do": [
            "Wander between two-story dark wooden lattice chaya buildings",
            "Visit Shima Teahouse museum preserved since the Edo period (1820)",
            "Taste gold-leaf wrapped pastries and matcha tea"
        ]
    },
    "tsuzumimon gate": {
        "tagline": "Architectural icon of Kanazawa Station",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "East Plaza of JR Kanazawa Station.",
        "things_to_do": [
            "Marvel at the 13.7-meter wooden gate shaped like a traditional Noh hand drum",
            "Photograph the futuristic glass Motenashi Dome framing the gate"
        ]
    },
    "takayama jinya": {
        "tagline": "Edo-period provincial government headquarters",
        "hours": "8:45 AM - 5:00 PM",
        "price_jpy": "¥440",
        "how_to_access": "10-minute walk from JR Takayama Station.",
        "things_to_do": [
            "Tour the only surviving Edo-era shogunate administrative office in Japan",
            "Inspect historic courtrooms, interrogation rooms, tatami halls, and rice granaries"
        ]
    },
    "miyagawa morning market": {
        "tagline": "Historic riverside morning market",
        "hours": "7:00 AM - 12:00 PM",
        "price_jpy": "Free",
        "how_to_access": "Along the Miyagawa River in central Takayama.",
        "things_to_do": [
            "Browse 70+ stalls run by local farmers and artisans",
            "Taste fresh apples, homemade pickles, and hot Hida beef steamed buns",
            "Pick up wooden Sarubobo amulets"
        ]
    },
    "sanmachi-suji": {
        "tagline": "Edo-period merchant district in the Hida mountains",
        "hours": "Open 24 hours (Shops 9:00 AM - 5:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "10-minute walk from JR Takayama Station.",
        "things_to_do": [
            "Stroll narrow lanes lined with dark wooden merchant houses with water flumes",
            "Sample A5 Hida beef nigiri sushi served on shrimp rice crackers",
            "Taste local sake at Funasaka or Harada Breweries under green cedar balls (Sugidama)"
        ]
    },
    "hida folk village": {
        "tagline": "Open-air museum of traditional thatched farmhouses",
        "hours": "8:30 AM - 5:00 PM",
        "price_jpy": "¥700",
        "how_to_access": "10-minute bus from Takayama Station on Sarubobo Bus.",
        "things_to_do": [
            "Explore 30+ relocated gassho-zukuri steep thatched-roof farmhouses",
            "Watch artisans crafting wooden handicrafts and straw shoes",
            "Stroll tranquil mountain pond surrounded by autumn maple leaves"
        ]
    },
    "shinhotaka ropeway": {
        "tagline": "Double-decker cable car into the Northern Alps",
        "hours": "8:30 AM - 4:00 PM",
        "price_jpy": "¥3,800",
        "how_to_access": "Nohi bus from Takayama Station to Shinhotaka Ropeway stop (approx 1h 40m).",
        "things_to_do": [
            "Ride Japan's only double-decker aerial tramway to 2,156m altitude",
            "Stand on the rooftop observation deck for 360° views of Mt. Hotaka and Mt. Yarigatake"
        ]
    },
    "meiji shrine": {
        "tagline": "Tranquil forest shrine in central Tokyo",
        "hours": "Sunrise to Sunset (approx. 6:00 AM - 4:30 PM in Nov)",
        "price_jpy": "Free",
        "how_to_access": "Right outside Harajuku Station (JR Yamanote) or Meiji-jingumae Station.",
        "things_to_do": [
            "Walk through giant cedar torii gates into a 70-hectare manmade sacred forest",
            "Photograph the giant wall of decorative sake barrels (kazaridaru)",
            "Write a wooden prayer plaque (ema) in the courtyard"
        ]
    },
    "harajuku": {
        "tagline": "Takeshita Street & Youth Streetwear Culture",
        "hours": "Open 24 hours (Boutiques 11:00 AM - 8:00 PM)",
        "price_jpy": "Free",
        "how_to_access": "Harajuku Station (JR Yamanote Line).",
        "things_to_do": [
            "Walk vibrant Takeshita Street and grab sweet rolled crepes (Marion Crepes)",
            "Explore backstreet fashion on Cat Street leading toward Shibuya",
            "Visit unique themed cafes and vintage clothing boutiques"
        ]
    },
    "miyashita park": {
        "tagline": "Elevated rooftop park, skatepark & shopping complex",
        "hours": "8:00 AM - 11:00 PM (Rooftop park)",
        "price_jpy": "Free",
        "how_to_access": "3-minute walk north of Shibuya Station.",
        "things_to_do": [
            "Relax on the open grassy rooftop park above Shibuya's train tracks",
            "Watch skaters at the rooftop skatepark and bouldering wall",
            "Grab street food at Shibuya Yokocho dining hall on the ground floor"
        ]
    },
    "shibuya crossing": {
        "tagline": "The world's busiest pedestrian scramble",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Directly outside Hachiko Exit of Shibuya Station.",
        "things_to_do": [
            "Walk across with up to 3,000 pedestrians per light cycle",
            "Greet the bronze Hachiko dog statue",
            "Photograph the intersection from Shibuya Scramble Square or Shibuya Hikarie"
        ]
    },
    "shibuya sky": {
        "tagline": "360° Rooftop observatory above Shibuya Crossing",
        "hours": "10:00 AM - 10:30 PM (Last entry 9:20 PM)",
        "price_jpy": "¥2,500 online (¥2,800 same-day)",
        "how_to_access": "14th floor entrance inside Shibuya Scramble Square skyscraper.",
        "things_to_do": [
            "Stand at 'Sky Edge' corner for iconic photos over Shibuya Crossing",
            "Lie on the Cloud Hammocks and view Tokyo Tower and Mt. Fuji on clear days",
            "Relax at the rooftop lounge as city lights sparkle at dusk"
        ]
    },
    "teamlab planets": {
        "tagline": "Immersive 'body immersive' digital art museum",
        "hours": "9:00 AM - 10:00 PM",
        "price_jpy": "¥4,400",
        "how_to_access": "1-minute walk from Shin-Toyosu Station (Yurikamome line).",
        "things_to_do": [
            "Wade barefoot through knee-deep water projected with glowing koi fish",
            "Immerse yourself in the Infinite Crystal Universe LED light maze",
            "Lie inside the floating floral dome with real floating orchids"
        ]
    },
    "omoide yokocho": {
        "tagline": "Memory Lane / Piss Alley - Post-war Izakaya alley",
        "hours": "Most stalls 4:30 PM - Midnight",
        "price_jpy": "¥2,000 - ¥4,000 per person",
        "how_to_access": "Northwest of Shinjuku Station West Exit.",
        "things_to_do": [
            "Squeeze into tiny 6-seat counters under glowing red lanterns",
            "Order charcoal-grilled yakitori skewers, tare beef tendon, and cold draft beer"
        ]
    },
    "golden gai": {
        "tagline": "Legendary maze of 200 micro-bars",
        "hours": "5:30 PM - 5:00 AM",
        "price_jpy": "¥500 - ¥1,000 cover charge + drinks",
        "how_to_access": "5-minute walk from Shinjuku Station East Exit, behind Hanazono Shrine.",
        "things_to_do": [
            "Explore six tiny alleys untouched by modern high-rise development",
            "Bar hop between themed 6-seat bars (punk rock, cinema, photography, jazz)"
        ]
    },
    "kabukicho": {
        "tagline": "Tokyo's famous neon entertainment district",
        "hours": "Open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "Shinjuku Station East Exit.",
        "things_to_do": [
            "Photograph the iconic Kabukicho Ichiban-gai red neon arch",
            "Spot the giant life-sized Godzilla head atop the Toho Cinema building"
        ]
    },
    "senso-ji temple": {
        "tagline": "Tokyo's oldest and most sacred Buddhist temple",
        "hours": "6:00 AM - 5:00 PM (Main hall) / Grounds open 24 hours",
        "price_jpy": "Free",
        "how_to_access": "5-minute walk from Asakusa Station (Ginza & Asakusa Subway Lines).",
        "things_to_do": [
            "Enter under the massive red lantern of Kaminarimon Gate",
            "Stroll Nakamise-dori shopping street for fresh rice crackers and ningyoyaki",
            "Purify hands at the dragon water fountain and waft incense from the Jokoro burner"
        ]
    },
    "akihabara": {
        "tagline": "Electric Town & global epicenter of anime / gaming culture",
        "hours": "10:00 AM - 9:00 PM",
        "price_jpy": "Free",
        "how_to_access": "Directly outside JR Akihabara Station (Electric Town Exit).",
        "things_to_do": [
            "Explore multi-story electronics chains (Yodobashi Camera Akiba)",
            "Shop character figures, manga, and retro games at Radio Kaikan & Mandarake",
            "Play claw machines, rhythm games, and fighting games at GiGO Arcades"
        ]
    },
    "tokyo tower": {
        "tagline": "Iconic 333-meter orange & white Eiffel-inspired tower",
        "hours": "9:00 AM - 10:30 PM",
        "price_jpy": "¥1,200 (Main Deck) / ¥3,000 (Top Deck Tour)",
        "how_to_access": "5-minute walk from Akabanebashi Station (Oedo Line).",
        "things_to_do": [
            "Ascend to the 150m Main Observation Deck and walk on glass floor panels",
            "Experience RED° TOKYO TOWER esports and VR park on floors 3-5",
            "Photograph the illuminated tower from Zojoji Temple grounds"
        ]
    }
}

# Schedule database for realistic, relaxed activity timing (accounting for transit & sunset)
ACTIVITY_SCHEDULES = {
    # Day 1: Nov 9 - Arrival
    "flight tokyo": ("15:45 - 17:00", "Landing at Haneda Airport, customs & transit"),
    "hotel toyoko inn": ("17:30 - 18:30", "Check-in, unpack & settle in"),
    
    # Day 2: Nov 10 - Osaka
    "train from tokyo to osaka": ("10:15 - 12:45", "Tokaido Shinkansen bullet train (Mt. Fuji views)"),
    "hotel hillarys shinsaibashi": ("13:15 - 14:00", "Check-in & drop luggage"),
    "kuromon market": ("14:15 - 15:45", "Late lunch & fresh seafood street market"),
    "shinsaibashi shopping street": ("16:00 - 17:15", "Leisurely stroll through covered arcade"),
    "glico man": ("17:30 - 18:00", "Sunset photo with iconic running man"),
    "dotonbori": ("18:00 - 19:00", "Canal walk as neon billboards light up"),
    "try street food in dotonbori": ("19:00 - 20:00", "Takoyaki & casual evening bites"),
    "shinsekai": ("20:15 - 21:30", "Retro neon district & Tsutenkaku Tower"),
    "torikizoku": ("21:30 - 22:45", "Yakitori dinner & relaxed drinks"),

    # Day 3: Nov 11 - Osaka
    "namba yasaka shrine": ("09:45 - 10:45", "Morning visit to giant lion-head stage"),
    "osaka castle": ("11:15 - 13:30", "Castle museum, stone ramparts & park grounds"),
    "fukutaro": ("13:45 - 15:00", "Relaxed okonomiyaki lunch"),
    "america-mura": ("15:15 - 16:45", "Youth fashion, vintage shops & Triangle Park"),
    "umeda sky building": ("17:15 - 19:00", "Floating Garden sunset (~16:45) & night skyline"),
    "snacks from convenience stores in osaka": ("19:15 - 19:45", "Quick konbini snack break"),
    "ichiran ramen": ("20:00 - 21:15", "Cozy tonkotsu ramen dinner"),
    "don quijote": ("21:30 - 22:45", "Ebisu Ferris wheel & late souvenir shopping"),

    # Day 4: Nov 12 - Koyasan
    "train to koyasan": ("09:00 - 10:45", "Nankai Limited Express + scenic cable car"),
    "koyasan shukubo daienin": ("11:00 - 11:45", "Temple check-in & drop daypacks"),
    "daimon gate": ("12:00 - 12:45", "Grand entrance gate to Mount Koya"),
    "danjo garan complex": ("13:00 - 14:15", "Konpon Daito Pagoda & sacred halls"),
    "kongobu-ji": ("14:30 - 15:45", "Banryutei dragon rock garden & sliding screens"),
    "reihokan museum": ("16:00 - 17:00", "Treasures, sacred mandalas & Buddhist art"),
    "temple meal at saizen-in": ("17:30 - 19:00", "Traditional Shojin Ryori vegetarian dinner"),
    "okunoin cemetery": ("19:15 - 20:45", "Atmospheric lantern walk through ancient cedars"),

    # Day 5: Nov 13 - Nara
    "train to nara": ("08:30 - 10:45", "Transit from Koyasan to Nara (store luggage in locker)"),
    "nakatanidou": ("11:00 - 11:45", "High-speed mochi pounding show & warm mochi"),
    "isui-en garden": ("12:00 - 13:15", "Tranquil stroll through Edo-period pond garden"),
    "parco okonomiyaki": ("13:30 - 14:45", "Relaxed lunch at cozy local shop"),
    "todai-ji": ("15:00 - 16:30", "Great Bronze Buddha & Nigatsu-do veranda panorama"),
    "nara park": ("16:30 - 17:15", "Interacting with friendly deer in afternoon light"),
    "katsuga taisha": ("17:15 - 18:00", "Lantern-lined shrine in the peaceful forest"),
    "train to kyoto": ("18:15 - 19:15", "Retrieve bags & scenic train to Kyoto"),
    "piece hostel sanjo": ("19:30 onwards", "Check-in at Kyoto base & rest"),

    # Day 6: Nov 14 - Kyoto (Gion & Higashiyama)
    "gion": ("09:30 - 10:45", "Quiet morning stroll through preserved streets"),
    "hanami-koji": ("10:45 - 11:30", "Historic teahouse lane"),
    "yasaka shrine": ("11:30 - 12:30", "Vibrant Gion guardian shrine grounds"),
    "hachidaimei gihey": ("12:45 - 14:15", "Traditional claypot rice multi-course lunch"),
    "ninenzaka & sannenzaka": ("14:30 - 16:00", "Cobbled merchant slopes & artisan pottery shops"),
    "kiyomizu-dera": ("16:15 - 18:30", "Historic wooden stage, sunset & autumn night light-up"),

    # Day 7: Nov 15 - Kyoto (Arashiyama & Kinkaku-ji)
    "arashiyama bamboo forest": ("07:30 - 08:45", "Early morning arrival to beat tour crowds"),
    "tenryu-ji": ("09:00 - 10:15", "UNESCO Zen temple & mountain-view garden"),
    "senko-ji temple": ("10:30 - 11:45", "Secluded hillside temple with river overlook"),
    "iwatayama monkey park": ("12:00 - 13:15", "Snow monkeys & panoramic Kyoto overlook"),
    "matcha tea sweets": ("13:30 - 14:30", "Riverbank matcha soft serve & rest"),
    "kinkaku-ji": ("15:15 - 16:45", "Golden Pavilion reflecting in the autumn pond"),
    "ramen sen-no-kaze": ("18:00 - 19:30", "Miso ramen set dinner"),

    # Day 8: Nov 16 - Kyoto (Fushimi Inari, Nanzen-ji & Pontocho)
    "fushimi-inari": ("08:30 - 11:00", "Hike through vermilion Torii gates to Yotsutsuji"),
    "nanzen-ji temple": ("11:45 - 13:15", "Zen complex & Suirokaku Roman-style aqueduct"),
    "philosophers path": ("13:30 - 14:45", "Leisurely stone canal walking path"),
    "honen-in": ("14:45 - 15:45", "Thatched gate & serene moss garden sanctuary"),
    "evening walk by the kamo river": ("16:30 - 17:30", "Relaxing twilight river stroll"),
    "pontocho": ("17:45 - 18:45", "Atmospheric lantern-lit dining alley"),
    "hiro yakiniku": ("19:00 - 21:00", "Kyoto Japanese BBQ dinner"),

    # Day 9: Nov 17 - Kanazawa
    "thunderbird to kanazawa": ("09:40 - 11:50", "Scenic Limited Express ride past Lake Biwa"),
    "the square hotel kanazawa": ("12:15 - 13:00", "Check-in & drop luggage"),
    "omicho market": ("13:00 - 14:30", "Explore Kanazawa's bustling seafood market"),
    "mori mori sushi": ("13:30 - 14:30", "Fresh Sea of Japan conveyor sushi lunch"),
    "d.t. suzuki museum": ("15:00 - 16:15", "Minimalist Zen architecture & Water Mirror Garden"),
    "21st century of contemporary art museum": ("16:30 - 18:15", "Modern art & Leandro Erlich's Swimming Pool"),
    "sushi ippei": ("19:00 - 20:45", "Intimate sushi dinner by local masters"),

    # Day 10: Nov 18 - Kanazawa
    "tsuzumimon gate": ("09:00 - 09:30", "Morning photo at Kanazawa Station's wooden drum gate"),
    "oyama shrine": ("09:45 - 10:45", "Unique Dutch stained-glass gate & gardens"),
    "kanazawa castle": ("11:00 - 12:15", "Feudal park grounds & reconstructed turrets"),
    "kenrouken garden": ("12:30 - 14:15", "Japan's top garden with November Yukitsuri snow ropes"),
    "hakuichi": ("14:15 - 14:45", "Edible 24K gold leaf soft-serve ice cream"),
    "higashi-chaya": ("15:15 - 17:15", "Preserved historic geisha teahouse district"),
    "ramen taiga": ("17:45 - 19:15", "Signature black miso ramen dinner"),

    # Day 11: Nov 19 - Takayama & Okuhida
    "train to takayama": ("08:15 - 10:15", "Scenic Limited Express train into Japanese Alps"),
    "miyagawa morning market": ("10:30 - 11:30", "Riverside market stalls & local mountain crafts"),
    "sanmachi-suji": ("11:45 - 13:15", "Old merchant streets, sake tasting & A5 Hida beef"),
    "takayama jinya": ("13:30 - 14:30", "Edo-period provincial government headquarters"),
    "hida folk village": ("15:00 - 16:30", "Traditional thatched gassho farmhouses"),
    "bus to okuhida onsen": ("17:00 - 18:15", "Scenic mountain bus up to Okuhida hot springs"),
    "yukimurasaki ryokan": ("18:30 onwards", "Ryokan check-in, open-air onsen bath & Kaiseki dinner"),

    # Day 12: Nov 20 - Takayama -> Tokyo
    "morning onsen & breakfast before checking out": ("08:00 - 09:30", "Unhurried breakfast & final morning onsen soak"),
    "shinhotaka ropeway": ("10:00 - 12:15", "Double-decker cable car into the Northern Alps"),
    "nishihotakaguchi observation deck": ("11:00 - 12:00", "360° summit views at 2,156m altitude"),
    "shinkansen to tokyo": ("14:00 - 18:30", "Transit to Toyama/Nagoya & bullet train to Tokyo"),
    "hotel metropolitan tokyo ikebukuro": ("19:00 onwards", "Check-in at Tokyo base & relaxed evening"),

    # Day 13: Nov 21 - Tokyo (Shibuya & Harajuku)
    "meiji shrine": ("09:30 - 11:00", "Tranquil morning walk through sacred evergreen forest"),
    "harajuku": ("11:15 - 12:30", "Takeshita Street & youth fashion boutiques"),
    "mipig cafe": ("12:45 - 13:45", "Playful micro pig cafe experience"),
    "miyashita park": ("14:00 - 15:30", "Rooftop green lawn, cafes & Cat Street walk"),
    "shibuya crossing": ("15:45 - 16:30", "World's busiest scramble crosswalk & Hachiko"),
    "shibuya sky": ("16:45 - 18:30", "Golden hour sunset & illuminated night skyline"),
    "sushi ten tokyo shibuya": ("19:00 - 21:00", "Omakase sushi dinner"),

    # Day 14: Nov 22 - Tokyo (Toyosu & Shinjuku)
    "teamlab planets": ("09:30 - 12:00", "Interactive digital art museum & water maze"),
    "udon shin": ("12:45 - 14:15", "Handcrafted artisan udon noodles lunch"),
    "cross shinjuku vision": ("14:30 - 15:15", "Watch the famous 3D giant calico cat"),
    "omoide yokocho": ("16:00 - 17:30", "Memory Lane: charcoal yakitori under red lanterns"),
    "kabukicho": ("17:45 - 19:15", "Shinjuku neon entertainment quarter & Godzilla head"),
    "golden gai": ("19:30 - 21:00", "Historic maze of 200 intimate micro-bars"),
    "kura sushi": ("21:15 - 22:30", "Conveyor belt sushi & capsule game fun"),

    # Day 15: Nov 23 - Tokyo (Asakusa, Akihabara & Tokyo Tower)
    "senso-ji temple": ("09:00 - 11:00", "Tokyo's oldest Buddhist temple & Nakamise-dori"),
    "akihabara": ("11:30 - 12:30", "Electric Town street atmosphere"),
    "radio kaikan": ("12:30 - 13:30", "Multi-floor anime & hobby merchandise"),
    "don quijote akihabara": ("13:30 - 14:30", "Discount megastore shopping"),
    "gigo arcade": ("14:30 - 15:30", "Classic Japanese arcades & claw games"),
    "tokyo tower": ("16:15 - 18:00", "Observation deck & twilight view of Tokyo"),
    "toranomon yokocho": ("18:30 - 20:30", "Gourmet dining hall dinner"),

    # Day 16: Nov 24 - Departure
    "last minute shopping": ("10:00 - 12:30", "Souvenirs at Tokyo Station / Daimaru depachika"),
    "train to haneda airport": ("13:00 - 13:45", "Transit to Haneda International Terminal 3"),
    "flight": ("16:00 onwards", "Check-in, Duty Free browsing & departure flight")
}

def normalize_key(name):
    """Normalize names for dictionary matching."""
    s = name.lower()
    # remove special chars
    s = re.sub(r'[\'\"’“”\-&,]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def clean_cost(cost_str):
    """Clean euro cost string into float or None."""
    if not cost_str:
        return None
    val = cost_str.replace('€', '').replace(',', '').strip()
    try:
        return float(val)
    except ValueError:
        return None

def main():
    csv_file = "/Users/jose.perez/Library/CloudStorage/OneDrive-ZEAL/Documents/Personal/Japan/PWA Japan Trip/source_itinerary.csv"
    
    rows = []
    with open(csv_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            
    # Group rows by Day
    day_groups = {}
    
    # Map day label to date
    for r in rows:
        day_str = r['Day'].strip()
        if not day_str or 'ic card' in r['Name'].lower():
            # Skip unassigned summary budget rows
            continue
        if day_str not in day_groups:
            day_groups[day_str] = []
        day_groups[day_str].append(r)

    days_output = []
    day_counter = 0

    for day_str, items in day_groups.items():
        day_counter += 1
        
        # Parse day number and city/subtitle from day_str
        m = re.match(r'Nov\s+(\d+)\s*-\s*(.*)', day_str)
        if m:
            day_num_day = int(m.group(1))
            subtitle = m.group(2).strip()
            date_str = f"2026-11-{day_num_day:02d}"
            display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %b %d")
        else:
            day_num_day = day_counter
            subtitle = day_str
            date_str = f"2026-11-{day_counter:02d}"
            display_date = f"Day {day_counter}"

        # Identify primary city for the day
        cities = [it['City'].strip() for it in items if it['City'].strip()]
        primary_city = cities[0] if cities else subtitle
        
        # Identify accommodation for this day (the user's chosen hotel)
        hotel_row = next((it for it in items if it['Activity'].strip().lower() == 'hotel'), None)
        hotel_info = None
        if hotel_row:
            hotel_info = {
                "name": hotel_row['Name'].strip(),
                "address": hotel_row['Address'].strip(),
                "maps_url": hotel_row['Google Maps'].strip(),
                "cost_eur": clean_cost(hotel_row['Cost']),
                "website": hotel_row['Website'].strip(),
                "notes": hotel_row['Details'].strip()
            }

        # Build items
        day_items = []
        item_order = 0
        for it in items:
            item_order += 1
            activity_type = it['Activity'].strip()
            raw_name = it['Name'].strip()
            norm = normalize_key(raw_name)
            
            # Lookup guidebook data
            guidebook_match = None
            for g_key, g_val in GUIDEBOOK_DATA.items():
                if g_key in norm or norm in g_key:
                    guidebook_match = g_val
                    break

            # Lookup realistic activity scheduled time
            sched_time = None
            pacing_note = None
            for s_key, s_val in ACTIVITY_SCHEDULES.items():
                if s_key in norm or norm in s_key:
                    sched_time = s_val[0]
                    pacing_note = s_val[1]
                    break
                    
            eur_val = clean_cost(it['Cost'])
            
            item_obj = {
                "id": f"day{day_counter}-{item_order}-{re.sub(r'[^a-zA-Z0-9]', '', raw_name)[:20].lower()}",
                "title": raw_name,
                "category": activity_type.lower() if activity_type else "other",
                "order": item_order,
                "city": it['City'].strip() or primary_city,
                "scheduled_time": sched_time,
                "pacing_note": pacing_note,
                "cost_eur": eur_val,
                "cost_jpy": guidebook_match.get("price_jpy") if guidebook_match else None,
                "address": it['Address'].strip() or None,
                "google_maps_url": it['Google Maps'].strip() or None,
                "website": it['Website'].strip() or None,
                "user_notes": it['Details'].strip() or None,
                "tagline": guidebook_match.get("tagline") if guidebook_match else None,
                "opening_hours": guidebook_match.get("hours") if guidebook_match else None,
                "how_to_access": guidebook_match.get("how_to_access") if guidebook_match else None,
                "highlights": guidebook_match.get("things_to_do", []) if guidebook_match else [],
                "travel_tip": guidebook_match.get("travel_tips") if guidebook_match else None,
                "calendar_event": {
                    "synced": False,
                    "event_id": None,
                    "summary": raw_name,
                    "time_start": sched_time.split(" - ")[0] if sched_time and " - " in sched_time else sched_time,
                    "time_end": sched_time.split(" - ")[1] if sched_time and " - " in sched_time else None
                }
            }
            day_items.append(item_obj)
            
        # Get curated tailored recommendations for this day
        tailored = TAILORED_RECOMMENDATIONS.get(day_counter, {
            "neighborhood": primary_city,
            "highlights": []
        })

        day_obj = {
            "day_index": day_counter,
            "date": date_str,
            "display_date": display_date,
            "title": f"Day {day_counter}: {subtitle}",
            "city": primary_city,
            "accommodation": hotel_info,
            "items": day_items,
            "tailored_recommendations": tailored
        }
        days_output.append(day_obj)

    # Master structure (Budget section removed)
    master = {
        "metadata": {
            "trip_name": "Japan Autumn Discovery 2026",
            "traveler": "Jose Perez",
            "start_date": "2026-11-09",
            "end_date": "2026-11-24",
            "total_days": len(days_output),
            "timezone": "Asia/Tokyo",
            "generated_at": datetime.utcnow().isoformat() + "Z"
        },
        "days": days_output,
        "travel_handbook": {
            "transport_tips": [
                {
                    "title": "IC Card (Suica / Pasmo)",
                    "detail": "On iPhone: Wallet App -> '+' -> Transit Card -> 'Suica' -> Load via Apple Pay. Tap ticket gates directly without unlocking phone. Works for subways, city buses, vending machines, and convenience stores."
                },
                {
                    "title": "Shinkansen Luggage Rules",
                    "detail": "Luggage with total dimensions (L+W+H) between 160cm and 250cm requires an oversized baggage seat reservation (rear row of car). Free when booking in advance via Smart-EX, but carries a ¥1,000 penalty if unreserved."
                },
                {
                    "title": "Luggage Forwarding (Takkyubin)",
                    "detail": "Yamato Transport ('Black Cat') sends large suitcases hotel-to-hotel overnight for ~¥2,000-¥3,000. Forward main luggage from Kyoto to Tokyo and travel light with daypacks to Kanazawa & Takayama!"
                },
                {
                    "title": "Cash vs. Card",
                    "detail": "While cards and IC cards are widely accepted in Tokyo & Osaka, shrines, temples (goshuin stamps, entry fees), small ramen ticket vending machines, and Takayama morning markets are strictly cash (Yen) only. 7-Eleven ATMs accept international cards with zero ATM fee."
                }
            ],
            "essential_apps": [
                {"name": "Google Maps", "desc": "Essential for live platform numbers, subway exits, and walking routes."},
                {"name": "Google Translate", "desc": "Camera live translation for Japanese menus and train signs."},
                {"name": "Smart-EX", "desc": "Official app to reserve and link Shinkansen tickets directly to your Suica."},
                {"name": "Japan Travel by NAVITIME", "desc": "Precise transit routing with JR Pass filters and station locker finders."}
            ]
        }
    }

    out_file = "/Users/jose.perez/Library/CloudStorage/OneDrive-ZEAL/Documents/Personal/Japan/PWA Japan Trip/master_itinerary.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    print(f"Successfully created {out_file} with {len(days_output)} days, scheduled activity times, and removed budget section!")

if __name__ == "__main__":
    main()

