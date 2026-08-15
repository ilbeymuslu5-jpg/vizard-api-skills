# Pablo Kanalı — OpenArt Üretim Rehberi

## Doğrulanmış üretim (15 Ağustos 2026)

Kanal açılış bumper'ı — **başarıyla üretildi**.

| Alan | Değer |
|---|---|
| historyId | `YH7KzMZ3gozcJLg4Nln7` |
| Model / mod | `pixverseV6` / `text2video` |
| Çıktı | 640x360, 5.04 sn, 24 fps, sessiz |
| Maliyet | **40 kredi** |

Kullanılan tam parametreler:

```json
{
  "model": "pixverseV6",
  "mode": "text2video",
  "params": {
    "prompt": "<PABLO-CHARACTER-BIBLE.md > Kilit Tanım + Stil Kilidi + sahne>",
    "videoCount": 1,
    "duration": 5,
    "resolution": "360p",
    "aspectRatio": "16:9",
    "generateAudio": false
  }
}
```

## Kredi tablosu (1 iş = 1 video, 5 sn)

| Model | Ayar | Kredi |
|---|---|---|
| PixVerse V6 | 360p, sessiz | **40** ← bütçe tabanı |
| PixVerse V6 | 540p, sessiz | 50 |
| Wan 2.7 | 720p | 125 |
| Kling 3 Omni | std + ses | 175 |
| Seedance 2.0 Mini | 720p + senkron ses | 200 |
| Seedance 2.0 | 720p + ses/lip-sync | 400 |

Görseller (karakter sayfası, thumbnail):

| Model | Ayar | Kredi |
|---|---|---|
| Kling 3 Omni | 1K | 10 |
| Seedream 4.5 | 2K | 15 |
| Nano Banana 2 | 1K | 20 |
| Nano Banana Pro | 1K, yazı için en iyi | 40 |

> Fiyatlar üretim anında kesinleşir; çözünürlük/süre/ses değişince değişir.

## Kalite yükseltme sırası

Bütçe geldikçe şu sırayla yükselt — etkisi en yüksek olandan:

1. **540p → 720p** (Wan 2.7, 125 kredi): 360p YouTube'da belirgin şekilde yumuşak kalıyor.
2. **Senkron ses** (Seedance 2.0 Mini, 200 kredi): çocuk içeriğinde müzik + efekt, izlenme süresini en çok artıran tek faktör.
3. **Karakter tutarlılığı** (image2video / element2video): önce Seedream 4.5 ile Pablo'nun key frame'ini üret (15 kredi), sonra o görseli referans vererek videoya çevir. Bölümler arası Pablo'nun aynı kalmasını sağlayan tek yöntem budur.

## Karakter tutarlılığı iş akışı (önerilen)

```
1. Seedream 4.5 text2image  → Pablo key frame (15 kredi)
2. OpenArt'a yükle          → visualReference al
3. Kling/Seedance element2video → Pablo'yu yeni sahnelerde oynat
```

`text2video` her seferinde Pablo'yu sıfırdan yorumlar — bölümler arası
farklılık yaratır. Kanal büyüyecekse 3. adıma geçmek şart.

## Sonraki sahne promptları

Her birinde `PABLO-CHARACTER-BIBLE.md` içindeki **Kilit Tanım** + **Stil Kilidi**
bloklarını başa birebir kopyala, sonra sahneyi ekle:

**S02 — Merak / kelebek**
> ...toddles through a sunlit meadow and stops as a big orange butterfly flutters
> down and lands on his nose. His eyes go wide with wonder, he goes cross-eyed
> looking at it, then giggles as the butterfly lifts off. Slow gentle side-tracking
> camera, dappled sunlight, floating pollen sparkles.

**S03 — Renk öğrenme**
> ...sits in the meadow and pulls three balloons from behind his back one by one —
> red, then blue, then yellow — holding each up to the camera and smiling. Static
> centered camera, clean uncluttered background for on-screen graphics.

**S04 — Uyku vakti (sakinleştirici)**
> ...curls up under a big soft leaf blanket as fireflies drift around him, yawns
> widely, his cap slipping over one eye, and slowly closes his eyes. Very slow
> camera drift, warm dim twilight, calm muted version of the palette.

**S05 — Sakarlık / komedi beat**
> ...tries to carry a stack of three round berries, wobbles, and they tumble out of
> his paws; he blinks in surprise, then laughs at himself. Static camera, bouncy
> exaggerated cartoon timing.
