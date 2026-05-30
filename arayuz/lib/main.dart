import 'package:flutter/material.dart';
import 'vip_terminal.dart'; // VIP Terminaline bağlantı

void main() {
  runApp(const SazlikApp());
}

class SazlikApp extends StatelessWidget {
  const SazlikApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Ghost CEO Paneli',
      theme: ThemeData.dark(),
      home: const VipTerminal(), // Tek bir 'const' yeterli!
    );
  }
}