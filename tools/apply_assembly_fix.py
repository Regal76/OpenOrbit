with open('server/assembly.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. filter ouroboros in visible()
old_vis = """        seen = set(out)
        return out + sorted(k for k in self.st['uretim'] if k in T and k not in seen)"""
new_vis = """        seen = set(out)
        out = out + sorted(k for k in self.st['uretim'] if k in T and k not in seen)
        return [k for k in out if k != 'recipe_blueprint-ouroboros']"""
assert old_vis in content, 'old_vis not found'
content = content.replace(old_vis, new_vis)

# 2. add up_content
old_content = """    def content(self):
        \"\"\"Girişteki tarif listesi (kayıttaki komutun yerine).\"\"\"
        keys = self.visible()
        self.shown = set(keys)
        return ('AssemblyRecipeContentModule', {'recipes': [self.recipe(k) for k in keys] + self.up.recipes()})"""
new_content = """    def content(self):
        \"\"\"Girişteki tarif listesi (kayıttaki komutun yerine).\"\"\"
        keys = self.visible()
        self.shown = set(keys)
        return ('AssemblyRecipeContentModule', {'recipes': [self.recipe(k) for k in keys] + self.up.recipes()})

    def up_content(self):
        \"\"\"Yükseltme sekmesindeki durum değişimlerinde yalnız yükseltme tarifleri (tüm 300+ tarifi göndermek istemcide kasmaya yol açar).\"\"\"
        return ('AssemblyRecipeContentModule', {'recipes': self.up.recipes()})"""
assert old_content in content, 'old_content not found'
content = content.replace(old_content, new_content)

# 3. collect_all
old_collect = "return msgs + ([self.content()] if self.up_state() != before else [])        # H61"
new_collect = "return msgs + ([self.up_content()] if self.up_state() != before else [])        # H61"
assert old_collect in content, 'old_collect not found'
content = content.replace(old_collect, new_collect)

# 4. handle
old_handle = """    def handle(self, name, f):
        self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.content
        if self.up.handles(name, f):
            before = self.up_state()
            msgs = self.up.handle(name, f)
            if self.up_state() != before:
                # hedefli yükseltme eklendi, atlandı ya da toplandı: istemci durum güncellemesini yalnız listesindeki (tarif, hedef)
                # satırına uygular ve Update/Upgrade panelini ancak tarif listesi gelince yeniden çizer (canlı test H39: Build'den
                # sonra yükseltme görünmüyordu; H61: Skip ve Collect'ten sonra panel eski sayaçta/"Collect"te kalıyordu)
                msgs = msgs + [self.content()]
            return msgs"""
new_handle = """    def handle(self, name, f):
        self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.up_content
        if self.up.handles(name, f):
            before = self.up_state()
            msgs = self.up.handle(name, f)
            if self.up_state() != before:
                # hedefli yükseltme eklendi, atlandı ya da toplandı: istemci durum güncellemesini yalnız listesindeki (tarif, hedef)
                # satırına uygular ve Update/Upgrade panelini ancak tarif listesi gelince yeniden çizer (canlı test H39: Build'den
                # sonra yükseltme görünmüyordu; H61: Skip ve Collect'ten sonra panel eski sayaçta/"Collect"te kalıyordu)
                msgs = msgs + [self.up_content()]
            return msgs"""
assert old_handle in content, 'old_handle not found'
content = content.replace(old_handle, new_handle)

# 5. tick
old_tick = "self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.content"
new_tick = "self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.up_content"
assert old_tick in content, 'old_tick not found'
content = content.replace(old_tick, new_tick)

with open('server/assembly.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('assembly.py updated successfully!')

# Now yukseltme.py
with open('server/yukseltme.py', 'r', encoding='utf-8') as f:
    up_content = f.read()

old_up_rec = "status=self.status(k, 0, now)) for k in list(UP) + list(DIS)]"
new_up_rec = "status=self.status(k, 0, now)) for k in list(UP) + list(DIS) if k != 'upgrade_upgrade-class2-ouroboros']"
assert old_up_rec in up_content, 'old_up_rec not found'
up_content = up_content.replace(old_up_rec, new_up_rec)

with open('server/yukseltme.py', 'w', encoding='utf-8') as f:
    f.write(up_content)
print('yukseltme.py updated successfully!')
