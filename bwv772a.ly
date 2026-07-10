% BWV 772a — triplet version (from Mutopia 772, NBA/ABRSM rhythm)
\version "2.24"
\include "english.ly"

voiceone = \relative c' {
r16 \tuplet 3/2 { c8 d8 e8 } \tuplet 3/2 { f8 e8 d8 } \tuplet 3/2 { c8 b8 c8 } g'8 |
\tuplet 3/2 { d8 a8 g,8 } \tuplet 3/2 { c8 b8 a8 } \tuplet 3/2 { g8 f8 g8 } d'8 |
\tuplet 3/2 { e8 g8 a8 } \tuplet 3/2 { e8 f8 g8 } \tuplet 3/2 { g8 e8 f8 } \tuplet 3/2 { c8 d8 e8 } |
\tuplet 3/2 { e8 c8 d8 } \tuplet 3/2 { a8 b8 c8 } \tuplet 3/2 { c8 a8 b8 } \tuplet 3/2 { fis8 g8 a8 } |
\tuplet 3/2 { a8 d,8 } \tuplet 3/2 { c'8 d8 } \tuplet 3/2 { b8 g8 a8 } \tuplet 3/2 { e8 fis8 g8 } |
\tuplet 3/2 { g8 a8 b8 } \tuplet 3/2 { b8 c8 d8 } \tuplet 3/2 { d8 b8 c8 } \tuplet 3/2 { b,8 a8 g8 } |
g8 r r4 r16 \tuplet 3/2 { g8 a8 b8 } \tuplet 3/2 { c8 b8 a8 } |
fis8 r r4 r16 \tuplet 3/2 { a8 b8 c8 } \tuplet 3/2 { d8 c8 b8 } |
b8 r r4 r16 \tuplet 3/2 { d8 c8 b8 } \tuplet 3/2 { a8 b8 c8 } |
c8 r r4 r16 \tuplet 3/2 { e8 d8 c8 } \tuplet 3/2 { b8 cis8 d8 } |
\tuplet 3/2 { cis8 d8 e8 } d8 \tuplet 3/2 { f8 b8 a,8 } |
\tuplet 3/2 { d8 gis8 fis,8 } \tuplet 3/2 { b8 c8 } d4 ~ |
\tuplet 3/2 { d8 fis8 e,8 } \tuplet 3/2 { a8 gis8 fis8 } \tuplet 3/2 { e'8 c8 d8 } \tuplet 3/2 { d8 b8 c8 } |
\tuplet 3/2 { c8 gis8 a'8 } \tuplet 3/2 { a8 f8 e8 } \tuplet 3/2 { gis,8 e8 f'8 } \tuplet 3/2 { c8 b8 a8 } |
\tuplet 3/2 { a8 g8 a'8 } \tuplet 3/2 { e8 f8 g8 } g2 ~ |
\tuplet 3/2 { g8 f8 e8 } \tuplet 3/2 { a8 g8 f8 } f2 ~ |
\tuplet 3/2 { f8 f8 g8 } \tuplet 3/2 { d8 e8 f8 } f2 ~ |
\tuplet 3/2 { f8 e8 d8 } \tuplet 3/2 { g8 f8 e8 } e2 ~ |
\tuplet 3/2 { e8 d8 c8 } \tuplet 3/2 { f8 e8 d8 } \tuplet 3/2 { d8 f8 e8 } \tuplet 3/2 { a8 g8 f8 } |
\tuplet 3/2 { f8 a8 g8 } \tuplet 3/2 { c8 b8 a8 } \tuplet 3/2 { c8 g8 } \tuplet 3/2 { e8 d8 c8 } |
\tuplet 3/2 { c8 a8 bes8 } \tuplet 3/2 { f8 g8 a8 } \tuplet 3/2 { a8 c8 b8 } \tuplet 3/2 { d8 f,8 c'8 } |
c1 |
}

voicetwo = \relative c {
r2 r16 \tuplet 3/2 { c8 d8 e8 } \tuplet 3/2 { f8 e8 d8 } |
\tuplet 3/2 { g'8 g,8 } r4 r16 \tuplet 3/2 { g'8 a8 b8 } \tuplet 3/2 { c8 b8 a8 } |
\tuplet 3/2 { b8 c8 d8 } c8 \tuplet 3/2 { e8 a8 g,8 } |
\tuplet 3/2 { c8 fis8 e,8 } \tuplet 3/2 { a8 b8 } c4 ~ |
\tuplet 3/2 { c8 e8 d,8 } \tuplet 3/2 { g8 fis8 e8 } \tuplet 3/2 { b,8 c8 d8 } g8 |
\tuplet 3/2 { e8 g8 fis8 } \tuplet 3/2 { b8 c8 } \tuplet 3/2 { d8 d,8 } |
r16 \tuplet 3/2 { g8 a8 b8 } \tuplet 3/2 { c8 b8 a8 } \tuplet 3/2 { g8 fis8 g8 } d'8 |
\tuplet 3/2 { a8 e8 d,8 } \tuplet 3/2 { g8 fis8 e8 } \tuplet 3/2 { d8 c8 d8 } a'8 |
\tuplet 3/2 { g,8 f8 g'8 } \tuplet 3/2 { d8 e8 f8 } \tuplet 3/2 { e8 f8 d8 } f8 |
\tuplet 3/2 { e8 g8 a8 } \tuplet 3/2 { e8 f8 g8 } \tuplet 3/2 { f8 g8 e8 } g8 |
\tuplet 3/2 { f8 a8 bes8 } \tuplet 3/2 { f8 g8 a8 } \tuplet 3/2 { a8 f8 g8 } \tuplet 3/2 { d8 e8 f8 } |
\tuplet 3/2 { f8 d8 e8 } \tuplet 3/2 { b8 c8 d8 } \tuplet 3/2 { d8 b8 c8 } \tuplet 3/2 { gis8 a8 b8 } |
\tuplet 3/2 { b8 e,8 } \tuplet 3/2 { d'8 e8 } \tuplet 3/2 { c8 a8 b8 } \tuplet 3/2 { fis8 gis8 a8 } |
\tuplet 3/2 { a8 b8 c8 } \tuplet 3/2 { c8 d8 e8 } \tuplet 3/2 { a,8 e'8 e,8 } e8 |
\tuplet 3/2 { a8 a,8 } r4 r16 \tuplet 3/2 { e''8 d8 c8 } \tuplet 3/2 { b8 cis8 d8 } |
d2 ~ \tuplet 3/2 { d8 b8 a8 } \tuplet 3/2 { d8 c8 b8 } |
b2 ~ \tuplet 3/2 { b8 c8 d8 } \tuplet 3/2 { a8 b8 c8 } |
c2 ~ \tuplet 3/2 { c8 a8 g8 } \tuplet 3/2 { c8 bes8 a8 } |
\tuplet 3/2 { bes8 a8 g8 } a8 \tuplet 3/2 { f8 c8 d'8 } |
\tuplet 3/2 { a8 e8 f'8 } \tuplet 3/2 { e8 e8 d,8 } \tuplet 3/2 { g8 f8 e8 } |
\tuplet 3/2 { c8 d8 e8 } e8 \tuplet 3/2 { f8 e8 d8 } \tuplet 3/2 { g8 g,8 } |
c1 |
}
