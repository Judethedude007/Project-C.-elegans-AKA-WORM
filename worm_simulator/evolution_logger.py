import csv
import datetime
import os


class EvolutionLogger:
	FIELDS = (
		"sim_time",
		"worms",
		"avg_energy",
		"total_births",
		"total_deaths",
		"lineages",
		"largest_colony",
		"dominant_lineage",
		"food_total",
		"food_density",
		"pheromone_density",
		"season",
		"temperature",
		"water_level",
		"oxygen_level",
	)

	def __init__(self, output_dir, prefix="evolution_run", flush_every=1):
		os.makedirs(output_dir, exist_ok=True)
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		self.csv_path = os.path.join(output_dir, f"{prefix}_{timestamp}.csv")
		self._file = open(self.csv_path, "w", newline="", encoding="utf-8")
		self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDS)
		self._writer.writeheader()
		self._rows_since_flush = 0
		self._flush_every = max(1, int(flush_every))

	def log(self, **kwargs):
		row = {field: kwargs.get(field, "") for field in self.FIELDS}
		self._writer.writerow(row)
		self._rows_since_flush += 1
		if self._rows_since_flush >= self._flush_every:
			self._file.flush()
			self._rows_since_flush = 0

	def close(self):
		if self._file and not self._file.closed:
			self._file.flush()
			self._file.close()
