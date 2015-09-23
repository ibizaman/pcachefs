#!/usr/bin/python

"""
   Range and Ranges classes used by pCacheFS

   Copyright 2012 Jonny Tyers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

"""

"""
# Represents a range of integers (i.e. a start and an end)
"""
class Range(object):
    def __init__(self, start, end):
        if start >= end:
            raise ValueError('start (' + str(start) + ') must be smaller than end (' + str(end) + ')')

        self.start = start
        self.end = end

        self.size = end - start

    def __repr__(self):
        return 'Range ' + str(self.start )+ '..' + str(self.end)

    def __cmp__(self, other):
        if type(other) == Range:
            if self.start == other.start:
                return cmp(self.end, other.end)
            return cmp(self.start, other.start)

        else:
            if self.start == other:
                return cmp(self.end, other)
            return cmp(self.start, other)

    def contains(self, i):
        if type(i) == Range:
            return i.start >= self.start and i.end <= self.end

        return i >= self.start and i <= self.end

"""
# A group of ranges.
#
# This class is a list with special awareness of Range objects. It will
# re-jig its contents as new Ranges are added to ensure that Ranges never
# overlap and are in order.
#
# For example:
#   ranges = Ranges()
#
#   ranges.add_range(Range(0, 3))
#   # ranges now just contains (0, 3)
#
#   ranges.add_range(Range(6, 10))
#   # ranges = (0,3) (6,10)
#
#   ranges.add_range(Range(7, 15))
#   # ranges = (0,3) (6,15)
#    # (6,10) and (7,15) overlap so they have been merged and the
#   # resulting range that is covered by both is added instead
#
#   ranges.add_range(Range(3, 5))
#   # ranges = (0,5) (6,15)
#   # (0,3) and (3,5) overlap, so they are merged
#
#   ranges.add_range(Range(5, 6))
#   # ranges = (0,15)
#   # (5,6) overlaps with both (0,5) and (6,15) so it is merged with both
#
#   ranges.add_range(Range(15, 16))
#   # ranges = (0,16)
#
#   ranges.add_range(Range(1, 3))
#   # ranges = (0,16)
#   # (1,3) is already included in our range so it is effectively ignored
#
"""
class Ranges(object):
    def __init__(self):
        self.ranges = []

        # start and end of the entire range (ie the start point of the
        # starting range to the end point of the finishing range)
        self.start = 0
        self.end = 0

    def __repr__(self):
        return str(self.ranges)

    def _cleanup(self):
        old_ranges = list(self.ranges)
        old_ranges.sort()

        i = 0
        while i < (len(old_ranges)-1):
            # get the next item, compare it with the item that follows it
            item = old_ranges[i]
            next_item = old_ranges[i+1]

            if item.end >= next_item.start:
                old_ranges.pop(i)
                old_ranges.pop(i) # effectively this removes item at i+1

                new_range = Range(item.start, max(item.end, next_item.end))
                old_ranges.append(new_range)
                old_ranges.sort()

            else:
                # only move to the next item of the list if we didn't modify
                # the current item
                i += 1

        self.ranges = old_ranges

        self.start = self.ranges[0].start
        self.end = self.ranges[-1].end

    def add_range(self, range):
        self.ranges.append(range)
        self._cleanup()

    """
    # Determines if i is contained within this list of ranges.
    #
    # if i is a number, then this will return True if it falls within
    # one of the Range objects within this Ranges object.
    #
    # If i is a Range object, this will return True if it falls *entirely*
    # with one of the Range objects within this Ranges object (i.e. its start
    # and end are completely 'inside' or equal to a Range in this Ranges).
    #
    """
    def contains(self, i):
        for r in self.ranges:
            if r.contains(i):
                return True

        return False

    """
    # Determine which parts of range are not covered by ranges within this Ranges object.
    #
    # For example, if I have this Ranges:
    #  (0,3) (5,10) (12,15)
    #
    # and I call:
    #  get_uncovered_portions(Range(2, 13))
    #
    # I get back a new Ranges object:
    #  (3,4) (10,12)
    #
    """
    def get_uncovered_portions(self, range):
        portions = []

        # if we have no ranges added then none of the given range will be covered
        if len(self.ranges) == 0:
            return [ range ]

        # if the search range doesn't overlap any items in this range this nothing
        # in this range will cover any of the search range
        if range.end <= self.start or range.start >= self.end:
            return [ range ]

        search_range = Range(range.start, range.end)
        i = 0
        while i < len(self.ranges):
            item = self.ranges[i]

            if item.contains(search_range):
                # if search_range is entirely contained, exit loop (return empty list)
                break

            elif not item.contains(search_range.start):
                # if search_range.start doesn't fall within this item, either
                # search_range begins before item.start, or after item.end

                if search_range.start < item.start:

                    if search_range.end < item.start:
                        # if search_range ends before this item (ie never overlaps)
                        # then add a portion representing the entire search_range and
                        # exit the loop, since we've now gone as far as the end of the
                        # search_range
                        portions.append(Range(search_range.start, search_range.end))
                        break

                    else:
                        # if search_range begins before this item starts (and it overlaps
                        # with this item), add a portion to account for the space between
                        # search_range.start and item.start, move beginning of search_range
                        # to item.start, and re-run loop without moving to the next item

                        portions.append(Range(search_range.start, item.start))
                        search_range = Range(item.start, search_range.end)

                else:
                    # if this item does not overlap search range at all, ignore this item
                    i += 1 # move to next item

            else:
                # if overlaps, then move the search_range up to begin at
                # the end of this item (since it is 'covered' up to the end of this
                # item)
                search_range = Range(item.end, search_range.end)

                # get the next item (because of _cleanup, we know that there will be
                # space between item and next_item)
                next_item = None
                if i < len(self.ranges)-1:
                    next_item = self.ranges[i+1]

                if next_item == None or search_range.end <= next_item.start:
                    # if our search_range finishes before we get to the next item, then add a
                    # portion for search_range, and exit (since we've finished)

                    portions.append(Range(search_range.start, search_range.end))
                    break

                else:
                    # if our search_range strays into the next_item range, add a portion
                    # to cover the space up to the beginning of the next item, then move
                    # the beginning of search_range up to the next item and re-run loop

                    portions.append(Range(search_range.start, next_item.start))
                    search_range = Range(next_item.start, search_range.end)

                    i += 1 # move to next item

        return portions

