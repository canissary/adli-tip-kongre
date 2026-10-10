# Adli Tıp Kongre Takvimi – Kurulum Rehberi

Bu paket, Türkiye ve yurt dışındaki adli tıp, adli bilimler ve sağlık hukuku kongre, sempozyum ve atölyelerini listeleyen web sitesini içerir. Site GitHub Pages üzerinde ücretsiz yayınlanır, herkese açıktır ve her pazartesi sabahı kendiliğinden güncellenir. Claude.ai üyeliğine bağlı değildir.

## Paketteki dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `index.html` | Sitenin kendisi |
| `data.json` | Etkinlik listesi (site bu dosyadan okur) |
| `feed.xml` | RSS beslemesi (yeni etkinlik bildirimleri için) |
| `scripts/update.py` | Haftalık arama ve güncelleme betiği |
| `.github/workflows/guncelle-ve-yayinla.yml` | Betiği her pazartesi çalıştıran ve siteyi yayınlayan otomasyon |

## Nasıl çalışır

Her pazartesi 08:49'da (İstanbul) GitHub, `update.py` betiğini çalıştırır. Betik, Claude API'nin web arama özelliğiyle dernek, kurum ve üniversite sitelerini tarar. Yeni etkinlikleri ve değişen tarihleri `data.json`'a yazar, siteyi yeniden yayınlar ve yenilik varsa size e-posta ile gelen bir duyuru (GitHub "issue") açar.

Claude API, Claude.ai üyeliğinden ayrı bir hizmettir: kullandıkça ödenir ve üyeliğiniz bitse de çalışmaya devam eder.

---

## Kurulum (yaklaşık 30 dakika)

### 1. GitHub hesabı açın
1. https://github.com/signup adresine gidin.
2. E-posta, şifre ve kullanıcı adı belirleyin. Kullanıcı adı site adresinizde görünecek (ör. `ferkongre` → `ferkongre.github.io`).
3. E-postanıza gelen kodla hesabı doğrulayın. Ücretsiz plan yeterli.

### 2. Yeni bir depo oluşturun
1. Sağ üstteki **+** → **New repository**.
2. Repository name: `adli-tip-kongre`
3. **Public** seçili olsun (ücretsiz yayın için gerekli).
4. **Create repository**.

### 3. Dosyaları yükleyin
1. Depo sayfasında **uploading an existing file** bağlantısına (veya **Add file → Upload files**) tıklayın.
2. Zip dosyasını bilgisayarınızda açın. `index.html`, `data.json`, `feed.xml`, `README.md` dosyalarını ve `scripts` klasörünü pencereye sürükleyin.
3. Altta **Commit changes**'e basın.

`.github` klasörü Windows ve Mac'te gizli olduğu için sürüklenmeyebilir. Bu yüzden otomasyon dosyasını elle oluşturun:

4. **Add file → Create new file**.
5. Dosya adı kutusuna tam olarak şunu yazın: `.github/workflows/guncelle-ve-yayinla.yml`
6. Zip içindeki aynı adlı dosyayı Not Defteri veya TextEdit ile açın, tüm içeriği kopyalayıp GitHub'daki kutuya yapıştırın.
7. **Commit changes**.

### 4. GitHub Pages'i açın
1. Depoda **Settings** → soldan **Pages**.
2. **Source** kısmında **GitHub Actions** seçin.

### 5. Claude API anahtarı alın
1. https://platform.claude.com adresinde hesap açın.
2. **Billing** bölümünden kredi yükleyin (önceden ödemeli; 5–10 dolar aylarca yeter).
3. Aynı yerden aylık harcama limiti koyun (ör. 10 dolar). Böylece beklenmedik fatura olmaz.
4. **API Keys** → **Create Key**. Anahtarı kopyalayın; bir daha gösterilmez.

### 6. Anahtarı GitHub'a gizli olarak ekleyin
1. Depoda **Settings** → **Secrets and variables** → **Actions**.
2. **New repository secret**.
3. Name: `ANTHROPIC_API_KEY`, Secret: kopyaladığınız anahtar.
4. **Add secret**. Anahtar gizli kalır; site ziyaretçileri göremez.

### 7. İlk çalıştırma
1. Depoda **Actions** sekmesi. Sorulursa otomasyonları etkinleştirin.
2. Soldan **Haftalık güncelle ve yayınla** → sağda **Run workflow** → **Run workflow**.
3. Birkaç dakika sonra yeşil tik görünür.
4. Siteniz: `https://KULLANICIADINIZ.github.io/adli-tip-kongre/`

Bundan sonra her pazartesi kendiliğinden çalışır.

---

## Bildirim almak ve doktorlara ulaştırmak

- **Size e-posta:** Depo sayfasında **Watch → Custom → Issues** seçin. Her yeni duyuruda e-posta gelir.
- **Doktorlar için:** GitHub hesabı olanlar aynı şekilde **Watch** yapabilir. Hesabı olmayanlar için RSS adresini kullanın: `https://KULLANICIADINIZ.github.io/adli-tip-kongre/feed.xml`
  - RSS'i e-posta bültenine çevirmek için Mailchimp'in "RSS kampanyası" veya Blogtrottr gibi ücretsiz servisler kullanılabilir. E-posta adresi topluyorsanız KVKK aydınlatma metni ekleyin.
  - Haftalık özeti WhatsApp veya Telegram grubuna elle iletmek de pratik bir yol: duyurunun (issue) metnini kopyalamanız yeterli.

## Elle etkinlik eklemek veya düzeltmek

1. Depoda `data.json` dosyasını açın, sağ üstteki kalem simgesine basın.
2. Mevcut bir etkinlik bloğunu kopyalayıp yapıştırın, bilgileri değiştirin. `id` benzersiz olsun; `added` alanına bugünün tarihini yazın.
3. **Commit changes**. Site bir iki dakika içinde güncellenir.

Bilinmeyen alanlar için `null` yazın. Tarih biçimi: `2027-05-18`.

## Maliyet

- GitHub ve GitHub Pages: ücretsiz.
- Claude API: web aramaları 1.000 arama başına 10 dolar; betik haftada en çok 25 arama yapar (ayda 1 dolar civarı). Buna metin işleme ücreti eklenir. Toplamın ayda birkaç dolar olması beklenir; kesin tutarı platform.claude.com'daki kullanım ekranından izleyin. Harcama limiti koymanızı öneririm.

## Sık karşılaşılan durumlar

- **Kırmızı çarpı (hata):** Actions sekmesinde çalışmaya tıklayıp hata mesajını okuyun. En sık neden: API anahtarı eksik ya da kredi bitmiş.
- **Model adı değişirse:** Anthropic eski modelleri zamanla kaldırır. **Settings → Secrets and variables → Actions → Variables** bölümünde `ANTHROPIC_MODEL` adlı bir değişken oluşturup güncel model adını yazın (güncel liste: https://platform.claude.com/docs).
- **Otomasyon durdu mu?** GitHub, 60 gün boyunca hiç değişiklik olmayan depolarda zamanlanmış görevleri kapatır. Betik her hafta en azından güncelleme tarihini değiştirdiği için bu normalde olmaz. Olursa Actions sekmesinden yeniden etkinleştirin.
- **Arama sayısını değiştirmek:** `ANTHROPIC_MODEL` gibi `MAX_SEARCHES` değişkeni ekleyebilirsiniz (varsayılan 25).
