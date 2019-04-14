from django.contrib import admin
from umbrella.models import Umbrella, UmbrellaShelf, UmbrellaShelf2Position
from django import forms


@admin.register(Umbrella)
class UmbrellaAdmin(admin.ModelAdmin):
    list_display = ['id', 'uid', 'status', 'color', 'category', 'type']
    list_filter = ['status', 'color', 'category', 'type']


class UmbrellaShelfForm(forms.ModelForm):
    class Meta:
        model = UmbrellaShelf
        fields = '__all__'

    def _save_m2m(self):
        """
        Save the many-to-many fields and generic relations for this form.
        """
        cleaned_data = self.cleaned_data
        exclude = self._meta.exclude
        fields = self._meta.fields
        opts = self.instance._meta
        # Note that for historical reasons we want to include also
        # private_fields here. (GenericRelation was previously a fake
        # m2m field).
        from itertools import chain
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if f.name in cleaned_data:
                f.save_form_data(self.instance, cleaned_data[f.name])

        for pos in range(1, self.instance.capacity + 1):
            pos_obj = UmbrellaShelf2Position(umbrella_shelf=self.instance,
                                            position=pos, status='0')
            pos_obj.save()

    def save(self, commit=True):
        if commit:
            self.instance.save()
            for pos in range(1, self.instance.capacity + 1):
                pos_obj = UmbrellaShelf2Position(umbrella_shelf=self.instance,
                                                position=pos, status='0')
                pos_obj.save()
        else:
            self.save_m2m = self._save_m2m
        return self.instance


@admin.register(UmbrellaShelf)
class UmbrellaShelfAdmin(admin.ModelAdmin):
    form = UmbrellaShelfForm

    list_display = ['id', 'loc_school', 'loc_position', 'capacity']
    list_filter = ['loc_school', 'loc_position', 'capacity']


class UmbrellaShelf2PositionForm(forms.ModelForm):
    class Meta:
        model = UmbrellaShelf2Position
        fields = '__all__'

    def _get_shelf_remaining_number(self, shelf):
        capacity = shelf.capacity
        used_number = UmbrellaShelf2Position.objects.filter(umbrella_shelf=shelf, status='1').count()
        return capacity - used_number
    
    def _umbrella_not_placed_yet(self, umbrella):
        return umbrella.status != '1'   # 伞未在架

    def _position_empty(self, shelf, position):
        if position > shelf.capacity or position < 1:
            raise forms.ValidationError('伞架{}的位置{}格式不对'.format(shelf, position))
        if UmbrellaShelf2Position.objects.filter(umbrella_shelf=shelf, position=position).count() != 1:
            raise forms.ValidationError('伞架{}存在多个位置：{}，或该位置不存在'.format(shelf, position))            
        obj = UmbrellaShelf2Position.objects.get(umbrella_shelf=shelf, position=position)
        return obj.status == '0'
        
    # def clean_umbrella_shelf(self):
    #     if self._get_shelf_remaining_number(self.umbrella_shelf) <= 0:
    #         raise forms.ValidationError('伞架{}已满'.format(self.umbrella_shelf))

    # def clean_position(self):
    #     if not self._position_empty(self.umbrella_shelf, self.position):
    #         raise forms.ValidationError('伞架{}的{}位置不为空或伞架位置格式不对'\
    #             .format(self.umbrella_shelf, self.position))

    # def clean_umbrella(self):
    #     if not self._umbrella_not_placed_yet(self.umbrella):
    #         raise forms.ValidationError('伞{}已在架'.format(self.umbrella))

    def clean(self):
        umbrella_shelf = self.cleaned_data.get('umbrella_shelf')
        umbrella = self.cleaned_data.get('umbrella')
        position = self.cleaned_data.get('position')
        status = self.cleaned_data.get('status')

        if self._get_shelf_remaining_number(umbrella_shelf) <= 0:
            raise forms.ValidationError('伞架{}已满'.format(umbrella_shelf))
        if status == '1' and not self._position_empty(umbrella_shelf, position):
            raise forms.ValidationError('伞架{}的{}位置不为空或伞架位置格式不对'.format(umbrella_shelf, position))
        if status == '1' and not self._umbrella_not_placed_yet(umbrella):
            raise forms.ValidationError('伞{}已在架'.format(umbrella))
        if status == '0' and umbrella:
            raise forms.ValidationError('若伞架位置上为无伞状态，则不要放伞'.format(umbrella))
        return self.cleaned_data
    def _save_m2m(self):
        """
        Save the many-to-many fields and generic relations for this form.
        """
        cleaned_data = self.cleaned_data
        exclude = self._meta.exclude
        fields = self._meta.fields
        opts = self.instance._meta
        # Note that for historical reasons we want to include also
        # private_fields here. (GenericRelation was previously a fake
        # m2m field).
        from itertools import chain
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if f.name in cleaned_data:
                f.save_form_data(self.instance, cleaned_data[f.name])
        if self.instance.umbrella and self.instance.umbrella.status != '1':
            umbrella = Umbrella.objects.get(pk=self.instance.umbrella.id)
            umbrella.status = '1'
            umbrella.save()

    def save(self, commit=True):
        if commit:
            self.instance.save()
            if self.instance.umbrella and self.instance.umbrella.status != '1':
                umbrella = Umbrella.objects.get(pk=self.instance.umbrella.id)
                umbrella.status = '1'
                umbrella.save()
        else:
            self.save_m2m = self._save_m2m
        return self.instance



@admin.register(UmbrellaShelf2Position)
class UmbrellaShelf2PositionAdmin(admin.ModelAdmin):
    form = UmbrellaShelf2PositionForm
    
    list_display = ['id', 'umbrella_shelf', 'position', 'status', 'umbrella']
    list_filter = ['status']
