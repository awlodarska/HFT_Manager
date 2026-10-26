# HFT Studio OS

Przestrzeń do zarządzania hafciarnią: produkcja, koszty, analityka i wycena w jednej aplikacji Streamlit. Ciemny motyw, responsywne kafelki, wykresy Plotly oraz lokalny zapis przez Pandas. Interfejs i kwoty są po polsku, w PLN.

## Uruchomienie

Python **3.11 lub 3.12**, Windows, Linux lub macOS. Blokady plików obsługuje wieloplatformowa biblioteka `filelock`; na Windowsie nie potrzebujesz WSL. W środowisku chmurowym używaj istniejącego katalogu repozytorium, bez tworzenia dodatkowego worktree.

### Windows — PowerShell

Otwórz PowerShell w rozpakowanym folderze aplikacji (tam, gdzie jest `app.py`):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Jeśli masz już środowisko `.venv`, pomiń pierwszy krok. Zatrzymaj działającą aplikację przez Ctrl+C przed aktualizacją. Aby sprawdzić instalację, uruchom `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`. W Git Bash odpowiednikiem ścieżki do Pythona jest `.venv/Scripts/python.exe`. Nie kopiuj `.venv` z Linuxa na Windows.

### Linux / macOS / środowisko chmurowe

```bash
cd /workspace/HFT_Manager
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Przy uruchamianiu z innego katalogu przejdź najpierw do katalogu projektu, aby Streamlit odczytał `.streamlit/config.toml`. Aplikacja nie potrzebuje kluczy API, bazy SQL ani zewnętrznych usług. Dla serwera chmurowego dodaj `--server.address 0.0.0.0 --server.port 8501`.

## Pierwsze kroki

- Aplikacja otwiera się od razu na Twoich danych. Nowa pracownia zaczyna od pustych list i zerowych KPI; nie ma trybu demonstracyjnego ani automatycznie generowanych wpisów.
- Dodaj klienta i łączną kwotę netto zlecenia. Wkłucia określają wartość **na sztukę**. Przełącznik FV/Paragon zapisuje rodzaj dokumentu; aplikacja nie wystawia faktur.
- W karcie zlecenia rozwiń **Zarządzaj zleceniem**, aby zmienić status. Usuwanie wymaga zaznaczenia potwierdzenia.
- Rejestruj koszty w wartości **brutto**. Eksport CSV obejmuje przefiltrowaną listę zleceń lub cały rejestr kosztów.

## Co oznaczają wyniki

Przychody oraz sprzedane sztuki uwzględniają wyłącznie status **Zrealizowane**. Nowe, produkowane i gotowe zlecenia pozostają w toku. Anulowane nie zwiększają przychodów. Okresy analizy bazują na **dacie utworzenia**, nie dacie zapłaty czy zmiany statusu. Daty zapisu korzystają z zegara serwera.

**Czysty zysk** jest uproszczonym wynikiem: przychód netto minus wydatki brutto. Nie jest wynikiem księgowym; nie rozlicza VAT, podatku dochodowego ani amortyzacji. Przed dodaniem pierwszych danych aplikacja pokazuje poprawne puste stany zamiast nieistniejących wyników.

Kalkulator wycenia **jedną sztukę**:

```text
czas [min] = wkłucia / prędkość + przygotowanie + zmiany kolorów × sekundy zmiany / 60
koszt pracy = czas / 60 × stawka godzinowa
koszt własny = odzież + koszt pracy + materiały
cena netto = koszt własny / (1 − marża / 100)
```

Domyślne założenia: 90 zł/h, 5 min przygotowania, 30 s na zmianę koloru, 1,50 zł materiałów. Możesz je zmienić w **Parametrach pracowni**. Dla 12 000 wkłuć przy 700/min, 3 zmianach koloru, odzieży za 25 zł i marży 35% wynik wynosi **95,33 zł netto/szt.** (23,64 min, koszt własny 61,96 zł). To marża od ceny sprzedaży, nie narzut na koszt. Dla serii rozdziel koszt jednorazowego przygotowania między sztuki. Cena nie zawiera VAT, programu hafciarskiego, dostawy ani rabatów.

## Dane i bezpieczeństwo zapisu

Domyślnie aplikacja tworzy katalog `data/` obok `app.py`. Możesz wskazać inny trwały katalog przez opcjonalną zmienną `HFT_DATA_DIR`. Przechowywane pliki:

| Plik | Kolumny |
| --- | --- |
| `orders.csv` | `id, created_at, client, product, quantity, stitches, net_amount, status, document` |
| `expenses.csv` | `id, created_at, category, supplier, gross_amount` |

ID to UUID, daty są zapisywane w ISO, CSV używa UTF-8, separatora przecinkowego i kropki dziesiętnej. Katalog danych i lokalne środowisko `.venv` są wyłączone z Git. Pliki powstają przy pierwszym zapisie. Usunięcie dawnego trybu demo nie kasuje istniejących CSV ani własnych wpisów użytkownika.

Zapis korzysta z blokady obejmującej odczyt i aktualizację oraz atomowego `os.replace`, co chroni przed utratą zmian z równoległych sesji na jednym serwerze. Braki opcjonalnych pól otrzymują bezpieczne wartości; błędne liczby, daty lub uszkodzone CSV wywołują czytelny komunikat i **nie są nadpisywane**. Tekst użytkownika jest escapowany w kartach HTML. Eksporty mają BOM dla Excela i neutralizują tekst mogący uruchomić formułę arkusza; oryginalne dane pozostają bez zmian.

Regularnie kopiuj katalog danych na trwały nośnik. Nie edytuj CSV ręcznie podczas działania aplikacji. To narzędzie dla zaufanej pracowni, bez logowania i separacji kont: przed udostępnieniem w publicznym Internecie zastosuj uwierzytelnianie na serwerze/proxy i HTTPS. Nie używaj współdzielonego dysku sieciowego bez sprawdzenia obsługi blokad i atomowej podmiany plików.

## Prywatny panel pod własną domeną

Docelowy adres może mieć postać `panel.hftstudio.pl`. Strona dla klientów na `hftstudio.pl` może pozostać u obecnego dostawcy. Osobny rekord DNS subdomeny kieruje wtedy do serwera aplikacji; nie trzeba zmieniać domeny głównej, poczty ani przenosić strony.

Sam adres i brak odnośnika na stronie nie zapewniają prywatności. Hosting panelu musi obsługiwać stale działający proces Streamlit, WebSocket, HTTPS, uwierzytelnianie właściciela przed dostępem do aplikacji oraz trwały katalog `HFT_DATA_DIR` z kopią zapasową. Port aplikacji powinien być dostępny wyłącznie przez uwierzytelniający serwer pośredniczący. Nie należy wystawiać obecnej aplikacji bez takiej ochrony.

Zwykły hosting strony/WordPressa może nie obsługiwać tego sposobu uruchamiania. Przed wdrożeniem potwierdź możliwości konkretnego pakietu lub wybierz osobny serwer. Hosting z nietrwałym dyskiem nie nadaje się do przechowywania firmowych CSV bez dodatkowego trwałego miejsca na dane. Jeśli przenosisz już używaną aplikację z komputera, skopiuj także własne `data/orders.csv` i `data/expenses.csv` bezpiecznym kanałem — pliki te celowo nie trafiają do GitHub.

Po wdrożeniu sprawdź w prywatnym oknie przeglądarki, że bez logowania nie da się zobaczyć panelu ani pobierać plików, a po zalogowaniu dane pozostają dostępne po restarcie serwera. Wdrożenie i ustawienie DNS wymagają dostępu do wybranego hostingu; sam kod w repozytorium nie uruchamia usługi internetowej.

## Testy

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Testy sprawdzają zapis i ponowny odczyt CSV, współbieżność, ochronę uszkodzonych plików, NaN, agregacje sprzedaży i kosztów, wzory wyceny oraz interakcje Streamlit przez `AppTest`. Korzystają z tymczasowych katalogów, bez zmieniania danych pracowni.

## Struktura

```text
app.py                  nawigacja, wybór danych, inicjalizacja
studio/ui.py            CSS, kafelki, wspólne komponenty i styl wykresów
studio/dashboard.py     KPI, wykres przychodów, struktura sprzedaży
studio/orders_view.py   formularz i zarządzanie zleceniami
studio/expenses_view.py rejestr kosztów i wykres kategorii
studio/pricing_view.py  interaktywny kalkulator
studio/storage.py       walidacja i trwały zapis CSV
studio/analytics.py     czyste funkcje agregujące
studio/pricing.py       model czasu, kosztów i marży
tests/                  testy jednostkowe i interfejsu
```
