import grf
from agrf.graphics.spritesheet import LazyAlternativeSprites


class FakeReferencedAction(grf.Action, grf.ReferenceableAction):
    def __init__(self, action, feature, ref_id=None):
        super().__init__()
        self.action = action
        self.feature = feature
        self.ref_id = ref_id

    def get_data(self, context):
        return self.action.get_data(context)

    def __str__(self):
        return f"ref {self.action.py(None)}"


class FakeReferencingAction(grf.Action, grf.ReferencingAction):
    def __init__(self, action, extra_refs):
        super().__init__()
        self.action = action
        self.extra_refs = extra_refs

    @property
    def feature(self):
        return self.action.feature

    def get_data(self, context):
        return self.action.get_data(context)

    def get_refs(self):
        yield from list(self.action.get_refs()) + self.extra_refs


class FakeAlternativeSprites(LazyAlternativeSprites, grf.ReferenceableAction):
    def __init__(self, sprite, feature, ref_id=None):
        super().__init__(sprite.voxel, sprite.part, *[s for s in sprite.sprites])
        self.feature = feature
        self.ref_id = ref_id

    def __str__(self):
        return f"alt {self.feature} {self.sprites[0].file.path} {self.sprites[0]}"


class FakeReferencingGenericSpriteLayout(grf.GenericSpriteLayout, grf.ReferencingAction):
    def __init__(self, feature, sprites, loading_sprites=None):
        if loading_sprites is None:
            ent1 = ent2 = tuple(range(31 - len(sprites), 31))
            loading_sprites = ()
        else:
            ent1 = tuple(range(31 - len(sprites) - len(loading_sprites), 31 - len(loading_sprites)))
            ent2 = tuple(range(31 - len(loading_sprites), 31))
        super().__init__(ent1=ent1, ent2=ent2)
        self._refs = (
            [
                FakeReferencedAction(
                    grf.Action1(
                        feature=feature, first_set=ent1[0], set_count=len(sprites), sprite_count=len(sprites[0])
                    ),
                    feature=feature,
                )
            ]
            + [FakeAlternativeSprites(l, feature=feature) for sl in sprites for l in sl]
            + [FakeAlternativeSprites(l, feature=feature) for sl in loading_sprites for l in sl]
        )

    def get_refs(self):
        yield from self._refs

    def set_refs(self, refs):
        self._refs = refs.copy()

    def __str__(self):
        return f"{self.feature} {self.ent1} {self.ent2}"
