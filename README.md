# AWFUL CODE WARNING!
This was created hastily, and that is reflected in the code. Furthermore, I do not think this method of animation is the best possible method, but it was the first one I thought of that actually worked and I didn't feel like implemented something better (say, a gradient based implementation).

# Building the level
Run `create_level.py` and the level should be written into a GMD file in the `product` directory. Almost certainly due to some error on my own part, this level won't actually work unless you open it in the editor and then exit and save it. The GMD file I have already placed in this repository's `product` directory does work as it is, though.

# How it works

`process_video.py` converts each frame of the video to pure black and white (no greyscale). For each frame, rather than display each pixel as a separate object, horizontal spans of pixels of the same color are displayed via one object that is horizontally (x) scaled. Using this method, the maximum number of objects required to display the most complex frame of the animation is 2,710. It is essential that this number remain relatively low to fit within the ~10,000 Group ID limit (triggers use up about 5,000 more ID's).

So, to generate each frame, we need to move each rectangle to a specific location and apply a specific horizontal scale. Given the video resolution of 512x384, there are ~1,023 possible X positions, 384 Y positions, and 512 horizontal scale factors. So, we create move and scale triggers for each possible permutation. With spawn trigger Group ID remapping, we can use these triggers to move each object to any location with any scale within the set range.

Lastly, for each object, three sequence triggers are created. The first one moves its associated object to a specific X position, the second to a specific Y position, and the third applies a specific scale. Every sequence trigger is called with the appropriate Group ID remapping at a rate of 30 calls per second (as the video's frame rate is 30 FPS).

### Extra Details

* A move trigger with target mode enabled resets the positions of all the objects for each frame.
* Scale triggers cannot easily be "reversed". Every scale trigger shares its Group ID with a spawn trigger that waits until the next frame to call an identical scale trigger but with "div by value X" enabled, thus "reversing" the first scale.
* Move triggers only accept integer offsets, so the objects are actually moved with follow triggers. The follow triggers cause the objects to follow two dummy objects: one that moves horizontally and the other vertically, each 1 unit in the positive direction on the respective axis.
* If an object is not needed in a specific frame (most frames do not use all of the available objects), the object's associated sequence triggers will call a no-op Group ID that does not trigger anything.
* On my PC, sequence triggers can't handle much more than 1,000 items, where an item is one combination of Group ID and number of times to call that group. So, any sequence trigger with more than 1,000 values is broken up into multiple sequence triggers. To ensure that the sequence triggers call their groups independently, most will lead with some number of no-op calls that matches the number of calls made by previous sequence triggers.
* To reduce the amount of information stored in the sequence triggers, I had to make the following optimization, or else I could not open the level. Whenever it reduces the number of objects that would have to be positioned and scaled to display a frame, the colors are swapped so that the objects can be used for the color that needs the fewest objects to be displayed.
    - Another sequence trigger is allotted for this, but uses very little memory in comparison to the other sequence triggers because in the grand scale of 6,572 frames, only ~87 frames call for color swaps. Thus the sequence trigger contains ~87 calls with different numbers of no-op calls between them.

# Recording the level

You'll be hard pressed to find a computer that can actually run this level. For me, I can run the level at 0.3x speed with any speed hack implementation (MegaHack v8, Cheat Engine, etc.). To record the level, I used [maxnut's renderer](https://github.com/maxnut/GDMegaOverlay) with my own lock delta modification (I just added `dt = 1.0f / 30;` as the first line of `void $modify(GJBaseGameLayer)::update(float dt)` in [src/Macrobot/Record.cpp](https://github.com/maxnut/GDMegaOverlay/blob/geode/src/Macrobot/Record.cpp)).
