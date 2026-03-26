# patrol_monitor

Программа обновляет табличку для патрулирующих, (почти всегда) не удаляя старые строки. Новые строки 
отмечаются жёлтым цветом (жёлтый превратится 
в бесцветный через 48 часов). Проверенные помечаются зелёным (и надписи в тексте меняются).

Вдохновлена на предложениях википедиста [Ailbeve](https://ru.wikipedia.org/wiki/Участник:Ailbeve)
(см. [обсуждение](https://ru.wikipedia.org/w/index.php?title=Обсуждение_Википедии:Запросы_к_патрулирующим#Периодически_проверять/публиковать_статьи_на_которые_ссылаются_правила)),
опирается на запросы в [Quarry](https://quarry.wmcloud.org).

Как применять: открываете https://quarry.wmcloud.org/query/103590, делаете форк в один клик
и запускаете, получаете таблицу. Её можно скачать как файл: Download Data > wikitable.

Далее скопируйте полученный файл в склонированный репозиторий, переименуйте его
в patrol-data-XXXX.wikitable, где XXXX - это ID querry (например 103590, как выше), далее он будет обновляться скриптом. 
Подождите, пока quarry станет отличаться после следующего запуска, 
скачайте новую версию и просто скопируйте в папку, после этого
запустите скрипт передав туда XXXX или patrol-data-XXXX.wikitable, 
patrol-data-XXXX.wikitable должна обновиться.

TODO: если зелёная уже держится неделю, то удалить; несколько файлов patrol_data_01.wikitable, patrol_data_02.wikitable, ... в лексикографическом порядке.

# English description

The program updates the table for patrollers (almost always) without removing old rows. New rows are highlighted in yellow (the yellow color will fade after 48 hours). Reviewed entries are marked in green (and the labels in the text are updated).

Inspired by suggestions from Wikipedian [Ailbeve](https://ru.wikipedia.org/wiki/Участник:Ailbeve)
(see [discussion](https://ru.wikipedia.org/w/index.php?title=Обсуждение_Википедии:Запросы_к_патрулирующим#Периодически_проверять/публиковать_статьи_на_которые_ссылаются_правила)),
and based on queries in [Quarry](https://quarry.wmcloud.org).

How to use: open https://quarry.wmcloud.org/query/103590, fork it with one click,
run it, and get the table. You can download it as a file: Download Data > wikitable.

Next, copy the resulting file into the cloned repository and rename it to
`patrol-data-XXXX.wikitable`, where `XXXX` is the query ID (for example, `103590`, as above). 
The file will then be updated by the script.

Wait until the Quarry output changes after the next run, download the new version, and simply copy it into the folder. 
After that, run the script, passing either `XXXX` or `patrol-data-XXXX.wikitable`. 
The file `patrol-data-XXXX.wikitable` will be updated.


TODO: if a row has been green for a week, delete it; support multiple files patrol_data_01.wikitable, patrol_data_02.wikitable, ... in lexicographic order.
