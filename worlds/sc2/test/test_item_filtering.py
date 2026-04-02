"""
Unit tests for item filtering like pool_filter.py
"""

import random
from types import SimpleNamespace

from .test_base import Sc2SetupTestBase
from ..item import item_groups, item_names, item_parents, StarcraftItem
from ..item.item_tables import item_table
from ..pool_filter import ValidInventory
from .. import options
from ..mission_tables import SC2Race

class ItemFilterTests(Sc2SetupTestBase):
    def test_excluding_all_barracks_units_excludes_infantry_upgrades(self) -> None:
        world_options = {
            'excluded_items': {
                item_groups.ItemGroupNames.BARRACKS_UNITS: -1,
            },
            'required_tactics': 'standard',
            'min_number_of_upgrades': 1,
            **self.TERRAN_CAMPAIGNS,
            'selected_races': {
                SC2Race.TERRAN.get_title()
            },
            'mission_order': 'grid',
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        races = {mission.race for mission in self.world.custom_mission_order.get_used_missions()}
        self.assertIn(SC2Race.TERRAN, races)
        self.assertNotIn(SC2Race.ZERG, races)
        self.assertNotIn(SC2Race.PROTOSS, races)
        itempool = [item.name for item in self.multiworld.itempool]
        self.assertNotIn(item_names.MARINE, itempool)
        self.assertNotIn(item_names.MARAUDER, itempool)

        self.assertNotIn(item_names.PROGRESSIVE_TERRAN_INFANTRY_WEAPON, itempool)
        self.assertNotIn(item_names.PROGRESSIVE_TERRAN_INFANTRY_ARMOR, itempool)
        self.assertNotIn(item_names.PROGRESSIVE_TERRAN_INFANTRY_UPGRADE, itempool)

    def test_excluding_one_item_of_multi_parent_doesnt_filter_children(self) -> None:
        world_options = {
            'locked_items': {
                item_names.DARK_TEMPLAR: 1,
                item_names.AVENGER: 1,
            },
            'excluded_items': {
                item_names.BLOOD_HUNTER: 1,
                # Exclude more items to make space
                item_names.CENTURION: 1,
                item_names.SENTINEL: 1,
                item_names.WRATHWALKER: 1,
                item_names.ENERGIZER: 1,
                item_names.AVENGER: 1,
                item_names.ARBITER: 1,
                item_names.VOID_RAY: 1,
                item_names.PULSAR: 1,
                item_names.DESTROYER: 1,
                item_names.DAWNBRINGER: 1,
            },
            'min_number_of_upgrades': 5,
            'required_tactics': 'standard',
            **self.ALL_CAMPAIGNS,
            'selected_races': {
                SC2Race.PROTOSS.get_title()
            },
            'mission_order': 'grid',
            'enable_race_swap': options.EnableRaceSwapVariants.option_shuffle_all,
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        itempool = [item.name for item in self.multiworld.itempool]
        self.assertIn(item_names.OPERATIONAL_EFFICIENCY_DARK_SHRINE, itempool)

    def test_excluding_all_items_in_multiparent_excludes_child_items(self) -> None:
        world_options = {
            'excluded_items': {
                item_names.ZEALOT: 1,
                item_names.SENTINEL: 1,
                item_names.CENTURION: 1,
            },
            'min_number_of_upgrades': 2,
            'required_tactics': 'standard',
            **self.PROTOSS_CAMPAIGNS,
            'selected_races': {
                SC2Race.PROTOSS.get_title()
            },
            'mission_order': 'grid',
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        itempool = [item.name for item in self.multiworld.itempool]
        self.assertNotIn(item_names.ZEALOT_SENTINEL_CENTURION_SHIELD_CAPACITY, itempool)
        self.assertNotIn(item_names.ZEALOT_SENTINEL_CENTURION_LEG_ENHANCEMENTS, itempool)

    def test_per_item_upgrade_limits_are_applied(self) -> None:
        world_options = {
            'locked_items': {
                item_names.MARINE: 1,
            },
            'required_tactics': options.RequiredTactics.option_no_logic,
            'min_number_of_upgrades': 0,
            'max_number_of_upgrades': -1,
            'upgrade_cull_mode': options.UpgradeCullMode.option_per_item,
            'min_number_of_upgrades_per_item': {
                item_names.MARINE: 1,
            },
            'max_number_of_upgrades_per_item': {
                item_names.MARINE: 1,
            },
            **self.TERRAN_CAMPAIGNS,
            'selected_races': {
                SC2Race.TERRAN.get_title()
            },
            'mission_order': 'grid',
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        world_item_names = [
            item.name
            for item in (self.multiworld.itempool + self.multiworld.precollected_items[self.player])
        ]
        marine_upgrades = set(item_parents.item_upgrade_groups[item_names.MARINE])
        marine_upgrade_count = sum(item_name in marine_upgrades for item_name in world_item_names)
        self.assertEqual(marine_upgrade_count, 1)

    def test_random_per_item_upgrade_limits_respect_range_and_overrides(self) -> None:
        world_options = {
            'locked_items': {
                item_names.MARINE: 1,
                item_names.MARAUDER: 1,
            },
            'required_tactics': options.RequiredTactics.option_no_logic,
            'min_number_of_upgrades': 1,
            'max_number_of_upgrades': 3,
            'upgrade_cull_mode': options.UpgradeCullMode.option_random_per_item,
            'min_number_of_upgrades_per_item': {
                item_names.MARINE: 2,
            },
            'max_number_of_upgrades_per_item': {
                item_names.MARINE: 2,
            },
            **self.TERRAN_CAMPAIGNS,
            'selected_races': {
                SC2Race.TERRAN.get_title()
            },
            'mission_order': 'grid',
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        world_item_names = [
            item.name
            for item in (self.multiworld.itempool + self.multiworld.precollected_items[self.player])
        ]
        marine_upgrades = set(item_parents.item_upgrade_groups[item_names.MARINE])
        marine_upgrade_count = sum(item_name in marine_upgrades for item_name in world_item_names)
        self.assertEqual(marine_upgrade_count, 2)

        marauder_upgrades = set(item_parents.item_upgrade_groups[item_names.MARAUDER])
        marauder_upgrade_count = sum(item_name in marauder_upgrades for item_name in world_item_names)
        self.assertGreaterEqual(marauder_upgrade_count, 1)
        self.assertLessEqual(marauder_upgrade_count, 3)

    def test_culled_variant_upgrades_are_removed(self) -> None:
        def option(value):
            return SimpleNamespace(value=value)

        variant_names = list(item_groups.colossus_variants)
        inventory_names = list(variant_names)
        for variant_name in variant_names:
            inventory_names.extend(item_parents.item_upgrade_groups.get(variant_name, []))
        inventory = [
            StarcraftItem(item_name, item_table[item_name].classification, item_table[item_name].code, self.player)
            for item_name in inventory_names
        ]

        world = SimpleNamespace(
            multiworld=None,
            player=self.player,
            random=random.Random(12345),
            options=SimpleNamespace(
                upgrade_cull_mode=option(options.UpgradeCullMode.option_global),
                min_number_of_upgrades=option(0),
                max_number_of_upgrades=option(-1),
                min_number_of_upgrades_per_item=option({}),
                max_number_of_upgrades_per_item=option({}),
                max_strains_per_zerg_unit=option(2),
                max_aspects_per_zerg_unit=option(2),
                max_variants_per_protoss_unit=option(1),
                kerrigan_max_active_abilities=option(99),
                kerrigan_max_passive_abilities=option(99),
                spear_of_adun_max_active_abilities=option(99),
                spear_of_adun_max_passive_abilities=option(99),
                nova_max_weapons=option(99),
                nova_max_gadgets=option(99),
                ensure_generic_items=option(0),
            ),
        )

        valid_inventory = ValidInventory(world, inventory)
        reduced_inventory = valid_inventory.generate_reduced_inventory(
            inventory_size=len(inventory),
            filler_amount=0,
            mission_requirements=[],
        )

        reduced_item_names = [item.name for item in reduced_inventory]
        present_variants = [name for name in variant_names if name in reduced_item_names]
        self.assertEqual(len(present_variants), 1)
        present_variant = present_variants[0]
        for variant_name in variant_names:
            if variant_name == present_variant:
                continue
            variant_upgrades = set(item_parents.item_upgrade_groups.get(variant_name, []))
            self.assertTrue(set(reduced_item_names).isdisjoint(variant_upgrades))

    def test_excluding_dark_templar_class_excludes_dark_templar_class_children(self) -> None:
        world_options = {
            'excluded_items': {
                item_names.DARK_TEMPLAR: 1,
                item_names.AVENGER: 1,
                item_names.BLOOD_HUNTER: 1,
            },
            'min_number_of_upgrades': 5,
            'required_tactics': 'standard',
            **self.PROTOSS_CAMPAIGNS,
            'selected_races': {
                SC2Race.PROTOSS.get_title()
            },
            'mission_order': 'grid',
        }
        self.generate_world(world_options)
        self.assertTrue(self.multiworld.itempool)
        itempool = [item.name for item in self.multiworld.itempool]
        self.assertNotIn(item_names.OPERATIONAL_EFFICIENCY_DARK_SHRINE, itempool)
