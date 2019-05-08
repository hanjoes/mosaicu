import argparse
from ipng import PNG
from random import randint


def generate_radius_indices(x_center, y_center, radius):
    result_indices = [(x_center, y_center)]

    x_min = x_center - 1
    y_min = y_center - 1
    x_max = x_center + 1
    y_max = y_center + 1

    for _ in range(radius):
        x_current = x_min
        y_current = y_min
        # go up
        while y_current <= y_max:
            result_indices.append((x_current, y_current))
            y_current += 1

        # go right
        x_current += 1
        y_current -= 1
        while x_current <= x_max:
            result_indices.append((x_current, y_current))
            x_current += 1

        # go down
        y_current -= 1
        x_current -= 1
        while y_current >= y_min:
            result_indices.append((x_current, y_current))
            y_current -= 1

        # go left
        x_current -= 1
        y_current += 1
        while x_current > x_min:
            result_indices.append((x_current, y_current))
            x_current -= 1

        x_min = x_min - 1
        y_min = y_min - 1
        x_max = x_max + 1
        y_max = y_max + 1

    return result_indices


def synchronize_radius(radius, index, bpp, bitmap, pixel, width, height):
    y_center, x_center = convert_to_2d(bitmap, bpp, index)
    # print(f'index:{index}, y_center:{y_center},x_center:{x_center}')
    radius_indices = generate_radius_indices(x_center, y_center, radius)
    for x, y in radius_indices:
        if 0 <= x < width and 0 <= y < height:
            i = convert_to_1d(bitmap, bpp, x, y)
            # print(f'x:{x}, y:{y}, i:{i}')
            pixel_at(i, bpp, lambda p: pixel, bitmap)


def pixel_at(index, bpp, pixel_transform, bitmap):
    """
    If pixel_transform is None, return the pixel. Otherwise apply transform to the pixel.

    :param index: index
    :param bpp: bytes per pixel
    :param pixel_transform: new pixel
    :param bitmap: the bitmap (list of bytearrays)
    :return: the updated pixel or the original pixel if pixel is None
    """
    row_index, pixel_index = convert_to_2d(bitmap, bpp, index)
    # print(f'row_index:{row_index}, pixel_index:{pixel_index}, index:{index}')
    selected_row = bitmap[row_index]
    selected_pixel = selected_row[pixel_index * bpp:(pixel_index + 1) * bpp]

    if pixel_transform:
        result_pixel = pixel_transform(selected_pixel)
        selected_row[pixel_index * bpp:(pixel_index + 1) * bpp] = result_pixel

    return selected_pixel


def convert_to_1d(bitmap, bpp, x, y):
    row_pixel_count = int(len(bitmap[0]) / bpp)
    return y * row_pixel_count + x


def convert_to_2d(bitmap, bpp, index):
    """
    Convert a one-dimensional pixel index to 2d (row index, and pixel index).
    :param bitmap: the bitmap
    :param bpp: bytes per pixel
    :param index: 1-dimensional index
    :return:
    """
    row_pixel_count = int(len(bitmap[0]) / bpp)
    row_index = int(index / row_pixel_count)
    pixel_index = index % row_pixel_count
    return row_index, pixel_index


def process(args):
    # TODO: recognize file formats
    png = PNG(file=args.pic)
    total_pixels = png.width * png.height
    # print(f'width:{png.width},height:{png.height},total_pixel:{total_pixels}')

    num_seeds = 300
    bpp = int(png.pixel_size_in_bit/8)
    for x in range(num_seeds):
        random_pixel_index = randint(0, total_pixels)
        seed_pixel = pixel_at(random_pixel_index, bpp, None, png.bitmap)
        synchronize_radius(15, random_pixel_index, bpp, png.bitmap, seed_pixel, png.width, png.height)

    png.render(output=args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI controls how sync behaves')
    parser.add_argument('--pic',
                        required=True,
                        help='input picture')
    parser.add_argument('--output',
                        required=True,
                        help='output file name')

    args = parser.parse_args()
    process(args)
