import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

const Color bgColor = Color(0xFF1E1E2F);
const Color cardColor = Color(0xFF27293D);
const Color neonOrange = Color(0xFFFF8D72);
const Color neonPink = Color(0xFFFD5D93);
const Color textPrimary = Colors.white;
const Color textSecondary = Colors.white54;

// Senin Codespaces API Adresin (Sonunda / olmadan)
const String apiUrl = "https://shiny-adventure-7w9qppj64whww9g-8000.app.github.dev";

class SazlikVipDashboard extends StatefulWidget {
  const SazlikVipDashboard({Key? key}) : super(key: key);

  @override
  State<SazlikVipDashboard> createState() => _SazlikVipDashboardState();
}

class _SazlikVipDashboardState extends State<SazlikVipDashboard> {
  final TextEditingController idController = TextEditingController();
  final TextEditingController gunController = TextEditingController();
  
  List<dynamic> musteriler = [];
  bool yukleniyor = true;

  @override
  void initState() {
    super.initState();
    _verileriCek(); // Ekran açılır açılmaz gerçek verileri getir
  }

  // API'den Müşteri Listesini Çek (GET)
  Future<void> _verileriCek() async {
    try {
      final response = await http.get(Uri.parse('$apiUrl/admin/musteriler'));
      if (response.statusCode == 200) {
        setState(() {
          musteriler = jsonDecode(response.body);
          // Listeyi en yeni eklenen en üstte olacak şekilde tersine çeviriyoruz (isteğe bağlı ama güzel durur)
          musteriler = musteriler.reversed.toList(); 
          yukleniyor = false;
        });
      }
    } catch (e) {
      print("Veri çekme hatası: $e");
      setState(() => yukleniyor = false);
    }
  }

  // API'ye Yeni Müşteri Gönder (POST) - GÜNCELLENDİ (HATA YAKALAYICI EKLENDİ)
  Future<void> _yeniMusteriEkle() async {
    if (idController.text.isEmpty || gunController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Lütfen ID ve Gün sayısını doldurun!")));
      return;
    }

    final body = jsonEncode({
      "kullanici_id": idController.text.toUpperCase(),
      "abonelik_gun_sayisi": int.tryParse(gunController.text) ?? 30
    });

    try {
      final response = await http.post(
        Uri.parse('$apiUrl/admin/musteri-yarat'),
        headers: {"Content-Type": "application/json"},
        body: body,
      );

      if (response.statusCode == 200) {
        final sonuc = jsonDecode(response.body);
        final uretilenSifre = sonuc["musteriye_verilecek_bilgiler"]["Sifre"];
        
        // Ekranda Şifreyi Göster (Garantici VIP Teslimat)
        _sifreyiEkrandaGoster(idController.text.toUpperCase(), uretilenSifre);
        
        idController.clear();
        gunController.clear();
        _verileriCek(); // Listeyi güncelle
      } else {
        // EĞER API HATA VERİRSE EKRANDA KIRMIZI UYARI ÇIKACAK
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text("Sunucu Hatası (${response.statusCode}): Bu ID zaten kullanılıyor olabilir mi?"),
          backgroundColor: neonPink,
        ));
      }
    } catch (e) {
      // EĞER BAĞLANTI KOPARSA EKRANDA KIRMIZI UYARI ÇIKACAK
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text("Bağlantı Hatası: API'ye ulaşılamıyor. URL'yi veya Portu kontrol et."),
        backgroundColor: neonPink,
      ));
    }
  }

  // Özel Şifre Uyarı Penceresi
  void _sifreyiEkrandaGoster(String id, String sifre) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: cardColor,
          title: Text("VİP MÜŞTERİ OLUŞTURULDU", style: GoogleFonts.poppins(color: Colors.greenAccent, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("ID: $id", style: const TextStyle(color: textPrimary, fontSize: 18)),
              const SizedBox(height: 10),
              Text("ŞİFRE: $sifre", style: const TextStyle(color: neonOrange, fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 2)),
              const SizedBox(height: 10),
              const Text("Bu şifreyi müşteriye iletin. Sistemde tekrar gösterilmeyecektir.", style: TextStyle(color: textSecondary, fontSize: 12)),
            ],
          ),
          actions: [
            TextButton(
              child: const Text("KAPAT", style: TextStyle(color: Colors.white)),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: bgColor,
      body: Row(
        children: [
          Container(
            width: 80,
            color: cardColor,
            child: Column(
              children: [
                const SizedBox(height: 20),
                Icon(Icons.shield, color: neonPink, size: 40),
                const SizedBox(height: 50),
                Icon(Icons.terminal, color: neonOrange, size: 28),
                const SizedBox(height: 30),
                Icon(Icons.people, color: textSecondary, size: 28),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("MERKEZİ VERİ YÖNETİMİ", style: GoogleFonts.poppins(color: textPrimary, fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 30),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        flex: 1,
                        child: Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(color: cardColor, borderRadius: BorderRadius.circular(12)),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("Yeni VIP Müşteri Yarat (Girdi)", style: GoogleFonts.poppins(color: neonOrange, fontSize: 16, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 20),
                              TextField(
                                controller: idController,
                                style: const TextStyle(color: Colors.white),
                                decoration: const InputDecoration(
                                  labelText: "Kullanıcı ID (Örn: ALFA-01)",
                                  labelStyle: TextStyle(color: textSecondary),
                                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: neonOrange)),
                                ),
                              ),
                              const SizedBox(height: 15),
                              TextField(
                                controller: gunController,
                                style: const TextStyle(color: Colors.white),
                                keyboardType: TextInputType.number,
                                decoration: const InputDecoration(
                                  labelText: "Abonelik Gün Sayısı (Örn: 30)",
                                  labelStyle: TextStyle(color: textSecondary),
                                  enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: neonOrange)),
                                ),
                              ),
                              const SizedBox(height: 20),
                              SizedBox(
                                width: double.infinity,
                                height: 50,
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(backgroundColor: neonOrange, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                                  onPressed: _yeniMusteriEkle,
                                  child: Text("SİSTEME KAYDET", style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1)),
                                ),
                              )
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 20),
                      Expanded(
                        flex: 2,
                        child: Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(color: cardColor, borderRadius: BorderRadius.circular(12)),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("Mevcut Aboneler (Çıktı)", style: GoogleFonts.poppins(color: neonPink, fontSize: 16, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 20),
                              yukleniyor 
                                ? const Center(child: CircularProgressIndicator(color: neonPink))
                                : musteriler.isEmpty 
                                  ? const Text("Henüz kayıtlı müşteri yok.", style: TextStyle(color: textSecondary))
                                  : ListView.builder(
                                shrinkWrap: true,
                                itemCount: musteriler.length,
                                itemBuilder: (context, index) {
                                  final musteri = musteriler[index];
                                  final bool aktifMi = DateTime.parse(musteri["abonelik_bitis"]).isAfter(DateTime.now());
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 10),
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                    decoration: BoxDecoration(
                                      color: bgColor,
                                      border: Border(left: BorderSide(color: aktifMi ? Colors.greenAccent : neonPink, width: 4))
                                    ),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(musteri["kullanici_id"], style: GoogleFonts.poppins(color: textPrimary, fontWeight: FontWeight.w600)),
                                        Text("Bitiş: ${musteri["abonelik_bitis"]}", style: GoogleFonts.poppins(color: textSecondary, fontSize: 12)),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: aktifMi ? Colors.greenAccent.withOpacity(0.1) : neonPink.withOpacity(0.1),
                                            borderRadius: BorderRadius.circular(4)
                                          ),
                                          child: Text(aktifMi ? "Aktif" : "Süresi Doldu", style: GoogleFonts.poppins(color: aktifMi ? Colors.greenAccent : neonPink, fontSize: 12, fontWeight: FontWeight.w600)),
                                        )
                                      ],
                                    ),
                                  );
                                },
                              )
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}