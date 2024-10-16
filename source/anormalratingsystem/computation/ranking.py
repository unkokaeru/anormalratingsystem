"""ranking.py: All ranking logic for the application."""

import json

from ..config.constants import Constants
from . import logger

logger = logger.getChild(__name__)


class ItemRanker:
    """
    A class to rank items based on user comparisons.

    Attributes
    ----------
    items : list[dict[str, str]]
        A list of dictionaries containing the items to rank.
    ratings : dict[str, int]
        A dictionary to keep track of the number of wins for each item.
    progress_file : str
        The file path to save and load progress.
    """

    def __init__(
        self,
        items: list[dict[str, str]],
        progress_file: str = Constants.DEFAULT_PROGRESS_SAVE_FILE,
    ):
        """
        Initializes the ItemRanker with items and a progress file.

        Parameters
        ----------
        items : list[dict[str, str]]
            A list of dictionaries containing the items to rank.
        progress_file : str, optional
            The file path to save and load progress,
            default is Constants.DEFAULT_PROGRESS_SAVE_FILE.
        """
        self.items = items
        self.ratings = {item["name"]: 0 for item in items}
        self.progress_file = progress_file
        self._load_progress()

    def _load_progress(self) -> None:
        """Load the ranking progress from a JSON file, if it exists."""
        try:
            with open(self.progress_file) as file:
                progress = json.load(file)
                self.ratings.update(progress)
                logger.info(f"Loaded progress from {self.progress_file}.")
        except FileNotFoundError:
            logger.warning("Progress file not found. Starting fresh.")

    def _save_progress(self) -> None:
        """Save the current ranking progress to a JSON file."""
        with open(self.progress_file, "w") as file:
            json.dump(self.ratings, file)
            logger.info(f"Saved progress to {self.progress_file}.")

    def _compare_items(self, item1: str, item2: str) -> str:
        """
        Prompt the user to compare two items and return the better one.

        Parameters
        ----------
        item1 : str
            The first item to compare.
        item2 : str
            The second item to compare.

        Returns
        -------
        str
            The better item as chosen by the user.
        """
        print(f"Compare:\n1. {item1}\n2. {item2}")
        while True:
            choice = input(f"Which is better? (1/2 or '{Constants.QUIT_TEXT}' to quit): ")
            if choice == "1":
                return item1
            elif choice == "2":
                return item2
            elif choice.lower() == Constants.QUIT_TEXT:
                self._save_progress()
                print("Progress saved. Exiting...")
                exit(0)
            else:
                print(f"Invalid choice. Please enter 1, 2, or '{Constants.QUIT_TEXT}'.")

    def _find_insert_position(self, ranked_items: list[str], item: str) -> int:
        """Find the position to insert an item into the ranked list using binary search."""
        low, high = 0, len(ranked_items)
        while low < high:
            mid = (low + high) // 2
            if ranked_items[mid] < item:
                low = mid + 1
            else:
                high = mid
        return low

    def estimate_comparisons_required(self) -> int:
        """
        Estimate the number of comparisons required to rank all items.

        Returns
        -------
        int
            The estimated number of comparisons required.
        """
        return len(self.items) * (len(self.items) - 1)

    def rank_items(self) -> list[dict[str, str]]:
        """
        Rank items based on user comparisons and return a list of ranked items.

        Returns
        -------
        list[dict[str, str]]
            A list of dictionaries containing the ranked items, where each dictionary
            has the item name and its corresponding rank.

        Notes
        -----
        This method ranks items using a comparison-based approach and distributes them
        into ten buckets according to a normal distribution. The process involves:
        1. Grouping the items into pairs and comparing them to determine the better item.
        2. Recursively applying the comparison process to the better items until a ranked list
        is formed.
        3. Inserting any remaining items into the ranked list using binary search.
        4. Distributing the ranked items into buckets based on a predefined weight distribution
        that favors the middle buckets, simulating a normal distribution.
        """
        if len(self.items) < 2:
            logger.error("Not enough items to rank.")
            return self.items

        # Compare items in pairs and determine the better item
        better_items = []
        for index in range(0, len(self.items), 2):
            if index + 1 < len(self.items):
                first_item_name = self.items[index]["name"]
                second_item_name = self.items[index + 1]["name"]
                better_item = self._compare_items(first_item_name, second_item_name)
                better_items.append(better_item)
            else:
                better_items.append(self.items[index]["name"])  # Unpaired item

        # Recursively apply the algorithm to the better items
        def recursive_rank(items: list[str]) -> list[str]:
            if len(items) < 2:
                return items

            better_items = []
            for index in range(0, len(items), 2):
                if index + 1 < len(items):
                    first_item = items[index]
                    second_item = items[index + 1]
                    better_item = self._compare_items(first_item, second_item)
                    better_items.append(better_item)
                else:
                    better_items.append(items[index])  # Unpaired item

            return recursive_rank(better_items)

        ranked_items = recursive_rank(better_items)

        # Insert remaining items into the ranked list
        for item in self.items:
            if item["name"] not in ranked_items:
                # Use binary search to find the correct position to insert
                insert_position = self._find_insert_position(ranked_items, item["name"])
                ranked_items.insert(insert_position, item["name"])

        # Define weights for normal distribution across 10 buckets
        total_weight = sum(Constants.RATING_WEIGHTS)
        total_items = len(ranked_items)

        # Calculate the number of items for each bucket based on weights
        bucket_sizes = [
            round((weight / total_weight) * total_items) for weight in Constants.RATING_WEIGHTS
        ]

        # Create buckets
        buckets: list[list[str]] = [[] for _ in range(len(bucket_sizes))]

        # Distribute items into buckets based on calculated sizes
        current_index = 0
        for bucket_index, bucket_size in enumerate(bucket_sizes):
            for _ in range(bucket_size):
                if current_index < len(ranked_items):
                    buckets[bucket_index].append(ranked_items[current_index])
                    current_index += 1

        # Create a dictionary of ranked items with their bucket number
        ranked_items_dict = {
            item: bucket_index for bucket_index, bucket in enumerate(buckets) for item in bucket
        }

        # Return the ranked items as a list of dictionaries
        return [{"name": item, "rank": str(rank)} for item, rank in ranked_items_dict.items()]
