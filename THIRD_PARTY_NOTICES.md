# Third-party notices

The two apps, RUSE Launcher and RUSE Studio, are free software under the GNU General Public License, version 3
([LICENSE](LICENSE)). An installed app carries this file and the licence beside its program.

## In the Studio, for showing the game's scripts as Python (the AI tab)

The Studio shows the game's map and mission scripts as Python through LittleGroove's engine (`src/ruse_mod_engine`,
GPL-3.0, from his RUSE Mod Manager), which does it with the libraries below. They are carried unchanged, at the versions
his RUSE Mod Manager pins (click at the newest), and their complete source is at the links.

| Library | Version | Licence | Copyright | Source |
|---|---|---|---|---|
| uncompyle6 | 3.9.3 | GPL-3.0 | Rocky Bernstein, hartmut Goebel, John Aycock | https://github.com/rocky/python-uncompyle6 |
| xdis | 6.1.8 | GPL-2.0 or any later version (used here under GPL-3.0) | Rocky Bernstein, hartmut Goebel | https://github.com/rocky/python-xdis |
| spark_parser | 1.9.0 | MIT | John Aycock, hartmut Goebel, Rocky Bernstein | https://github.com/rocky/python-spark |
| six | 1.17.0 | MIT | Benjamin Peterson | https://github.com/benjaminp/six |
| click | 8.5.0 | BSD-3-Clause | Pallets | https://github.com/pallets/click |

The GPL's text is in [LICENSE](LICENSE). The other licences' texts, as each library ships them:

### spark_parser (MIT)

```
Copyright (c) 1998-2002 John Aycock
Copyright (c) 2000 by hartmut Goebel <h.goebel@crazy-compilers.com>
Copyright (c) 2015, 2024 by Rocky Bernstein

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

### six (MIT)

```
Copyright (c) 2010-2024 Benjamin Peterson

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

### click (BSD-3-Clause)

```
Copyright 2014 Pallets

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

3.  Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## The other libraries the apps carry

Python itself and the other libraries in [installers/requirements.txt](installers/requirements.txt) (numpy, the
window library and what they need) come under their own licences; their list here is still to be written.
