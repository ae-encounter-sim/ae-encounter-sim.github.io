function binarySearch(number_list, lb, rb, value) {
	var midway = Math.floor((lb + rb) / 2);
	if (value > number_list[number_list.length - 1]['end_range']) {
		return { 'name' : number_list[number_list.length - 1]['name'], 'rarity' : number_list[number_list.length - 1]['rarity'] };
	} else if (value >= number_list[midway]['start_range'] && value < number_list[midway]['end_range']) {
		return { 'name' : number_list[midway]['name'], 'rarity' : number_list[midway]['rarity'] };
	} else if (value < number_list[midway]['start_range']) {
		return binarySearch(number_list, lb, midway, value);
	} else {
		return binarySearch(number_list, midway, rb, value);
	}
}