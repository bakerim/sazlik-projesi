import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fl_chart/fl_chart.dart'; // Eğer hata verirse terminale 'flutter pub add fl_chart' yaz

class VipTerminal extends StatefulWidget {
  const VipTerminal({super.key});

  @override
  State<VipTerminal> createState() => _VipTerminalState();
}

class _VipTerminalState extends State<VipTerminal> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      body: Row(
        children: [
          // SOL PANEL: KONSOL & NABIZ
          Container(
            width: 300,
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(color: Color(0xFF161B22)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("GHOST CEO // SİSTEM", style: GoogleFonts.robotoMono(color: Colors.cyanAccent)),
                const SizedBox(height: 40),
                _buildNabiz("SİSTEM GÜVENLİĞİ", "98%"),
                _buildNabiz("AMİRAL SİNYALLERİ", "12 Aktif"),
                const Spacer(),
                const Text("SÜRE: 28 GÜN KALDI", style: TextStyle(color: Colors.white24)),
              ],
            ),
          ),
          
          // SAĞ PANEL: GRAFİK & VERİ AKIŞI
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(30.0),
              child: Column(
                children: [
                  // ÜST: CANLI TREND GRAFİĞİ
                  Expanded(
                    flex: 1,
                    child: Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(color: Color(0xFF161B22), borderRadius: BorderRadius.circular(12)),
                      child: LineChart(LineChartData(
                        lineBarsData: [LineChartBarData(spots: [FlSpot(0, 30), FlSpot(1, 70), FlSpot(2, 40), FlSpot(3, 90)], isCurved: true, color: Colors.cyanAccent)],
                      )),
                    ),
                  ),
                  const SizedBox(height: 20),
                  // ALT: SİNYAL AKIŞI
                  Expanded(
                    flex: 1,
                    child: Container(
                      color: Color(0xFF161B22),
                      child: ListView(
                        children: [
                          _buildSinyalRow("AAPL", "GÜÇLÜ AL", "+2.4%"),
                          _buildSinyalRow("NVDA", "BEKLE", "-0.1%"),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNabiz(String baslik, String deger) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 15),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(baslik, style: TextStyle(color: Colors.white54, fontSize: 10)),
      Text(deger, style: GoogleFonts.robotoMono(color: Colors.white, fontSize: 20)),
    ]),
  );

  Widget _buildSinyalRow(String hisse, String durum, String oran) => ListTile(
    title: Text(hisse, style: TextStyle(color: Colors.white)),
    trailing: Text("$durum | $oran", style: TextStyle(color: Colors.cyanAccent)),
  );
}