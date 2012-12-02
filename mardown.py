text = """
A title on top
==============

Then some [lorem ipsum](http://en.wikipedia.org/wiki/Lorem_ipsum) dolor sit amet, consectetur adipiscing elit. Aenean a odio mauris, eget dignissim felis. Nunc eu justo dolor, a faucibus ante. Vivamus placerat, ligula eu cursus pellentesque, sem odio aliquam ante, ac blandit nulla turpis eu ipsum. Quisque tempus faucibus eros, ac egestas purus facilisis consectetur. Sed venenatis lacus et turpis gravida egestas eget a turpis. Mauris nunc est, tempus mattis lacinia id, posuere id mi. Pellentesque et eros a turpis lacinia venenatis ac id libero. Pellentesque hendrerit quam ac orci tristique gravida. Praesent et urna ac quam consequat consequat. Donec ut felis justo. Aliquam porttitor metus vitae odio faucibus vitae iaculis erat tristique.

Sed eros tortor, blandit at porta eu, feugiat sed massa. Vestibulum placerat vehicula sem id pharetra. Quisque porta varius condimentum. Nullam viverra orci quis massa porttitor aliquet. Maecenas id quam nisl. Etiam justo eros, suscipit a vestibulum gravida, euismod non mi. Nulla viverra sem et libero bibendum rutrum. Aliquam eget tincidunt mi. Suspendisse gravida pellentesque erat. Quisque semper tristique nunc quis venenatis. Nulla dignissim sapien dapibus enim auctor consectetur. Donec nec ipsum lacus. Praesent bibendum nunc vitae risus laoreet semper. In quam tellus, hendrerit quis dictum ac, euismod eget lorem.


        something('indented', by_itself)
        x = 12 * some_value

Sed eros tortor, blandit at porta eu, feugiat sed massa. Vestibulum placerat vehicula sem id pharetra. Quisque porta varius condimentum. Nullam viverra orci quis massa porttitor aliquet. Maecenas id quam nisl. Etiam justo eros, suscipit a vestibulum gravida, euismod non mi. Nulla viverra sem et libero bibendum rutrum. Aliquam eget tincidunt mi. Suspendisse gravida pellentesque erat. Quisque semper tristique nunc quis venenatis. Nulla dignissim sapien dapibus enim auctor consectetur. Donec nec ipsum lacus. Praesent bibendum nunc vitae risus laoreet semper. In quam tellus, hendrerit quis dictum ac, euismod eget lorem.


```python
import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Point, GraphicException
from random import random
from math import sqrt


def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist < steps:
        return None
    o = []
    m = dist / steps
    for i in xrange(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.extend([lastx, lasty])
    return o
```

Sed eros tortor, blandit at porta eu, feugiat sed massa. Vestibulum placerat vehicula sem id pharetra. Quisque porta varius condimentum. Nullam viverra orci quis massa porttitor aliquet. Maecenas id quam nisl. Etiam justo eros, suscipit a vestibulum gravida, euismod non mi. Nulla viverra sem et libero bibendum rutrum. Aliquam eget tincidunt mi. Suspendisse gravida pellentesque erat. Quisque semper tristique nunc quis venenatis. Nulla dignissim sapien dapibus enim auctor consectetur. Donec nec ipsum lacus. Praesent bibendum nunc vitae risus laoreet semper. In quam tellus, hendrerit quis dictum ac, euismod eget lorem.

Here is a link:
        http://hygge.io

Another one: [hygge.io](http://hygge.io)

Sed eros tortor, blandit at porta eu, feugiat sed massa. Vestibulum placerat vehicula sem id pharetra. Quisque porta varius condimentum. Nullam viverra orci quis massa porttitor aliquet. Maecenas id quam nisl. Etiam justo eros, suscipit a vestibulum gravida, euismod non mi. Nulla viverra sem et libero bibendum rutrum. Aliquam eget tincidunt mi. Suspendisse gravida pellentesque erat. Quisque semper tristique nunc quis venenatis. Nulla dignissim sapien dapibus enim auctor consectetur. Donec nec ipsum lacus. Praesent bibendum nunc vitae risus laoreet semper. In quam tellus, hendrerit quis dictum ac, euismod eget lorem.


"""




import requests
import json
import jinja2


template = jinja2.Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title></title>
<meta name="viewport" content="width=device-width">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
<div class="span_12">
{{content}}
</body>
</html>
""")



data = json.dumps({
'text': text,

})
resp = requests.post("https://api.github.com/markdown", data=data)
print resp.status_code
with open("out.html", "w") as f:
    f.write(template.render(content=resp.content))






















































