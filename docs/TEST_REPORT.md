# TEST_REPORT — Fase 5 (protótipo)

- **Data:** 2026-11-07
- **Commit testado:** `30c5b50d` (os commits seguintes só mexem em `.gitignore` e documentação)
- **ISO:** `d77orphaned-live-x86_64-20261107.iso`, 1 664 143 360 bytes (1,6 GiB), sha256 `37b324352fd8f65fdca499e9d193b9b1917af7d36a0b22bd5fa2de4ad9a3f79d`
- **Build:** host Ubuntu 24.04 com xbps 0.60 estático, como root. O kernel do host não monta vfat, por isso a imagem EFI foi escrita com mtools (ver commit `34c90c87`). Repositórios: Void current e nonfree, mais o d77void (SourceForge).
- **VM:** QEMU 8, **sem KVM** (emulação pura), 2 vCPU, 3 GiB, VGA std, rede user (SLIRP). Arranque até ao login: cerca de 150 s.
- **Ferramentas:** `tests/qemu-harness.py`, `tests/check-tools.sh`, `tests/integrity-prepare.sh`, `tests/integrity-check.sh`.
- **Não testado:** hardware real (T12) e persistência (fora da PoC base).

## Resultados

| # | Teste | Resultado | Evidência |
|---|---|---|---|
| T1 | Manifesto | **PASSA** | 450 pacotes instalados; nenhum de `udisks2 udiskie gvfs NetworkManager ollama calamares pipewire sddm pulseaudio zfs hashcat d77run plymouth`; sem módulo dracut `autoinstaller` |
| T2 | Arranque BIOS | **PASSA** | Menu isolinux com as entradas normal, RAM, *graphics disabled*, *console only* e Memtest86+; o arranque por defeito chega à sessão pwm |
| T3 | Arranque UEFI | **PASSA (parcial)** | Com OVMF chega à sessão pwm, o que só é possível pelo `EFI/BOOT/BOOTX64.EFI`. A captura do menu GRUB aos 60 s saiu preta: o menu não ficou confirmado visualmente |
| T4 | `d77.nogui` | **PASSA** | `sv status greetd` → `down`; os restantes serviços correm; TTY e consola série utilizáveis |
| T5 | `nomodeset` + pwm | **FALHA** | O Xorg carrega `fbdev`/`vesa` mas o pwm não fica a correr e o ecrã fica preto (modo texto 720×400). **Não investigado** |
| T6 | Autologin pwm → greeter → wasp + Utumno | **PASSA, com uma falha não explicada** | O autologin no pwm funciona (barra pwm). O Kantele abre em X11 com `~/.config/pwm/config.toml`. O wasp + Utumno arranca pelo greeter, com «weather unavailable» (D1), em 2 de 3 tentativas; na outra, o login no wasp acabou na sessão pwm, sem causa identificada. O Kantele em Wayland não chegou a ser testado: o comando de teste usou um `WAYLAND_DISPLAY` errado |
| T7 | Bibliotecas e comandos | **PASSA** | 1499 executáveis ELF sem bibliotecas em falta; todos os comandos prometidos existem |
| T8 | Integridade dos discos alvo | **PASSA** | Discos de teste: ext4 e XFS com journal sujo, NTFS, LUKS2, RAID1 MD, LVM, swap. Depois de um arranque completo com sessão gráfica: nenhum MD assemblado, nenhum dispositivo device-mapper, nada montado, swap desligada, journal ext4 ainda sujo; **SHA-256 dos 8 discos idêntico antes e depois** |
| T9 | Montagem segura | **PASSA** | `blockdev --setro` + `mount -o ro,noload` (ext4) e `ro,norecovery` (XFS); o journal continua sujo; hashes inalterados |
| T10 | Rede | **PASSA (VM)** | DHCP automático (`10.0.2.15/24`, rota e DNS), ping ao gateway OK, nenhuma porta TCP à escuta (sshd inativo). O chrony não sincronizou: o SLIRP não deixa passar NTP. Wi-Fi não testado |
| T11 | Sem persistência | **PASSA** | Todos os arranques acima foram feitos sem partição de dados |
| T12 | Hardware real | **POR FAZER** | Do lado do utilizador (T480s/Libreboot) |

## Defeitos encontrados pelos testes e corrigidos

1. **LVM ativado no arranque** (T8, primeira execução: LV `tvg-tlv` ativo). O `03-filesystems.sh` do runit-void corre `vgchange --sysinit -a ay` em todos os arranques, fora do udev. Correção: `postsetup.sh` põe `auto_activation_volume_list = []` e `event_activation = 0` no `lvm.conf`. Nesse mesmo script, o `mdadm -As` não assemblou o RAID graças ao `AUTO -all`.
2. **pwm saía em ~2 s** (T6: o autologin terminava e aparecia o greeter). O pwm executa `xmodmap -pke` ao arrancar e sai com `Io(NotFound)` sem ele. O pacote `pwm` não declara `xmodmap` e o `xorg-minimal` não o traz. Correção: `xmodmap` no manifesto. **Sugestão fora deste repositório:** acrescentar `xmodmap` aos `depends` do template do pwm no srcpkgs-d77.
3. **wasp não arrancava sem GPU** (T6: `Software rendering detected … couldn't create renderer`). O scenefx precisa de EGL/GLES e recusa o llvmpipe. Correção: `WLR_RENDERER_ALLOW_SOFTWARE=1` em `/etc/profile.d/`, que o greetd carrega antes de cada sessão.
4. **Imagem EFI vazia sem erro** (build). O `mklive.sh` herdado montava a `efiboot.img` com os erros descartados. Correção: a montagem é verificada, há alternativa pelas mtools e o build falha se não houver `BOOTX64.EFI`.

## Em aberto

- **T5 `nomodeset`:** ecrã preto e o pwm não fica a correr. Possíveis causas, nenhuma verificada: o Xorg sem KMS escolhe um driver que falha na VGA std do QEMU, ou o greeter (dwl) volta a falhar sem `/dev/dri` e o greetd entra em ciclo.
- **T6 intermitente:** uma de três tentativas de login no wasp pelo greeter acabou no pwm. O log do greetd vai para o syslog e não há daemon de syslog na ISO; numa segunda volta convém deixar o greetd a registar com `svlogd` para apanhar isto.
- **Cosmético:**
  - no wasp com renderização por software, o fundo mostra restos do greeter, e há um bloco preto à esquerda da barra da Utumno;
  - o widget de rede da Utumno diz «offline» porque lê o estado do NetworkManager, que a ISO não tem; o DHCP funciona.
- **Tamanho:** a ISO tem 1,6 GiB, acima da estimativa de 0,9 a 1,1 GiB do gate.
