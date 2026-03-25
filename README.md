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
в patrol_data.wikitable (далее он будет обновляться скриптом). Подождите, пока quarry станет 
отличаться, скачайте новую версию и просто скопируйте в папку, после этого
запустите скрипт, patrol_data.wikitable должна обновиться.

TODO: если зелёная уже держится неделю, то удалить.

# English description

The program updates the table for patrollers (almost always) without removing old rows. New rows are highlighted in yellow (the yellow color will fade after 48 hours). Reviewed entries are marked in green (and the labels in the text are updated).

Inspired by suggestions from Wikipedian [Ailbeve](https://ru.wikipedia.org/wiki/Участник:Ailbeve)
(see [discussion](https://ru.wikipedia.org/w/index.php?title=Обсуждение_Википедии:Запросы_к_патрулирующим#Периодически_проверять/публиковать_статьи_на_которые_ссылаются_правила)),
and based on queries in [Quarry](https://quarry.wmcloud.org).

How to use: open https://quarry.wmcloud.org/query/103590, fork it with one click,
run it, and get the table. You can download it as a file: Download Data > wikitable.

Then copy the downloaded file into the cloned repository and rename it to
`patrol_data.wikitable` (it will be updated by the script afterward). Wait until the Quarry
output changes, download the new version, and simply copy it into the folder. After that,
run the script — `patrol_data.wikitable` will be updated.

TODO: if a row has been green for a week, delete it.
