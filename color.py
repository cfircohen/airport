import webcolors


def Color(name):
  """Return BGR value for given color name"""
  return webcolors.name_to_rgb(name)[::-1]
