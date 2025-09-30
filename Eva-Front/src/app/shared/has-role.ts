import { Directive, Input, TemplateRef, ViewContainerRef, inject, effect } from '@angular/core';
import { TokenStorage } from '@services/token-storage';

@Directive({
  selector: '[appHasRole]',
})
export class HasRole {
  private tpl = inject(TemplateRef<any>);
  private vcr = inject(ViewContainerRef);
  private store = inject(TokenStorage);

  private roleWanted: 'company' | 'candidate' | 'any' = 'any';

  @Input() set appHasRole(role: 'company' | 'candidate' | 'any') {
    this.roleWanted = role;
    this.render();
  }

  constructor() {
    effect(() => this.render()); // re-render cuando cambie el usuario en TokenStorage
  }

  private render() {
    const me = this.store.me;
    const ok = this.roleWanted === 'any' || (me && me.role === this.roleWanted);

    this.vcr.clear();
    if (ok) this.vcr.createEmbeddedView(this.tpl);
  }
}
