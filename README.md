# Another Eden Encounter Simulator

Try your luck at the gacha at [https://ae-encounter-sim.github.io/](https://ae-encounter-sim.github.io/); select a banner and go for a lone enounter or 10 pull!

## How does this work? (in general)

* Links to the official rates on each encounter banner are provided by WFS in-game (the More Details button on the banner in the Gallery of Dreams)
* These rates are scraped from those pages and used to assign a valid range to a particular character/rarity for both lone encounters and the 10th encounter
	* See the JSON files in the [banners](https://github.com/ae-encounter-sim/ae-encounter-sim.github.io/tree/master/banners) folder if curious about the raw data
* When an encounter is requested, the webpage generates random number(s) between 0 and 1 and searches the list of rates to find the range they fall between
* Then you get a character image with name and rarity (because it wouldn't be any fun without the images and stars!)

## How does this work? (more technical)

* Scraping is done by a script in the [python](https://github.com/ae-encounter-sim/ae-encounter-sim.github.io/tree/master/python) folder, which also creates ranges for characters for both lone and 10th encounters
* The webpage primarily runs javascript/jQuery and utilizes the Bootstrap framework
* Images are extracted from game files; see the [Datamine page](https://reddit.com/r/AnotherEdenGlobal/wiki/index/datamine#datamine) on r/AnotherEdenGlobal to learn the basics

### Updates

See [New Banners](https://github.com/ae-encounter-sim/ae-encounter-sim.github.io/wiki/New-Banners) for info on adding new banners