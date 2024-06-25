/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import {
  ComponentFixture,
  fakeAsync,
  TestBed,
  tick,
} from '@angular/core/testing';

import { DownloadReportZipComponent } from './download-report-zip.component';
import { of } from 'rxjs';
import { MatDialogRef } from '@angular/material/dialog';
import { DownloadZipModalComponent } from '../download-zip-modal/download-zip-modal.component';
import { Router } from '@angular/router';
import { TestRunService } from '../../services/test-run.service';
import { Routes } from '../../model/routes';
import { RouterTestingModule } from '@angular/router/testing';
import { Component } from '@angular/core';
import { MOCK_PROGRESS_DATA_COMPLIANT } from '../../mocks/testrun.mock';

describe('DownloadReportZipComponent', () => {
  let component: DownloadReportZipComponent;
  let fixture: ComponentFixture<DownloadReportZipComponent>;
  let compiled: HTMLElement;
  let router: Router;

  const testrunServiceMock: jasmine.SpyObj<TestRunService> =
    jasmine.createSpyObj('testrunServiceMock', ['downloadZip']);

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        RouterTestingModule.withRoutes([
          { path: 'risk-assessment', component: FakeRiskAssessmentComponent },
        ]),
        DownloadReportZipComponent,
      ],
      providers: [{ provide: TestRunService, useValue: testrunServiceMock }],
    }).compileComponents();
    fixture = TestBed.createComponent(DownloadReportZipComponent);
    router = TestBed.get(Router);
    compiled = fixture.nativeElement as HTMLElement;
    component = fixture.componentInstance;
    component.url = 'localhost:8080';
    component.data = MOCK_PROGRESS_DATA_COMPLIANT;
  });

  describe('Class tests', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    describe('#onClick', () => {
      beforeEach(() => {
        testrunServiceMock.downloadZip.calls.reset();
      });

      it('should call service if profile is a string', fakeAsync(() => {
        const openSpy = spyOn(component.dialog, 'open').and.returnValue({
          afterClosed: () => of(''),
        } as MatDialogRef<typeof DownloadZipModalComponent>);

        component.onClick(new Event('click'));

        expect(openSpy).toHaveBeenCalledWith(DownloadZipModalComponent, {
          ariaLabel: 'Download zip',
          data: {
            hasProfiles: false,
            profiles: [],
          },
          autoFocus: true,
          hasBackdrop: true,
          disableClose: true,
          panelClass: 'initiate-test-run-dialog',
        });

        tick();

        expect(testrunServiceMock.downloadZip).toHaveBeenCalled();
        openSpy.calls.reset();
      }));

      it('should navigate to risk profiles page if profile is null', fakeAsync(() => {
        const openSpy = spyOn(component.dialog, 'open').and.returnValue({
          afterClosed: () => of(null),
        } as MatDialogRef<typeof DownloadZipModalComponent>);

        fixture.ngZone?.run(() => {
          component.onClick(new Event('click'));

          expect(openSpy).toHaveBeenCalledWith(DownloadZipModalComponent, {
            ariaLabel: 'Download zip',
            data: {
              hasProfiles: false,
              profiles: [],
            },
            autoFocus: true,
            hasBackdrop: true,
            disableClose: true,
            panelClass: 'initiate-test-run-dialog',
          });

          tick();

          expect(router.url).toBe(Routes.RiskAssessment);
          openSpy.calls.reset();
        });
      }));

      it('should do nothing if profile is undefined', fakeAsync(() => {
        const openSpy = spyOn(component.dialog, 'open').and.returnValue({
          afterClosed: () => of(undefined),
        } as MatDialogRef<typeof DownloadZipModalComponent>);

        component.onClick(new Event('click'));

        expect(openSpy).toHaveBeenCalledWith(DownloadZipModalComponent, {
          ariaLabel: 'Download zip',
          data: {
            hasProfiles: false,
            profiles: [],
          },
          autoFocus: true,
          hasBackdrop: true,
          disableClose: true,
          panelClass: 'initiate-test-run-dialog',
        });

        tick();

        expect(testrunServiceMock.downloadZip).not.toHaveBeenCalled();
        openSpy.calls.reset();
      }));
    });

    it('should have title', () => {
      component.ngOnInit();

      expect(component.tooltip.message).toEqual(
        'Download zip for Testrun # Delta 03-DIN-CPU 1.2.2 22 Jun 2023 9:20'
      );
    });
  });

  describe('DOM tests', () => {
    it('should open risk profiles modal on click', () => {
      const openSpy = spyOn(component.dialog, 'open');
      compiled.click();

      expect(openSpy).toHaveBeenCalled();

      openSpy.calls.reset();
    });

    describe('tooltip', () => {
      it('should be shown on mouseenter', () => {
        const spyOnShow = spyOn(component.tooltip, 'show');
        fixture.nativeElement.dispatchEvent(new Event('mouseenter'));

        expect(spyOnShow).toHaveBeenCalled();
      });

      it('should be shown on focusin', () => {
        const spyOnShow = spyOn(component.tooltip, 'show');
        fixture.nativeElement.dispatchEvent(new Event('focusin'));

        expect(spyOnShow).toHaveBeenCalled();
      });

      it('should be hidden on mouseleave', () => {
        const spyOnHide = spyOn(component.tooltip, 'hide');
        fixture.nativeElement.dispatchEvent(new Event('mouseleave'));

        expect(spyOnHide).toHaveBeenCalled();
      });

      it('should be hidden on focusout', () => {
        const spyOnHide = spyOn(component.tooltip, 'hide');
        fixture.nativeElement.dispatchEvent(new Event('focusout'));

        expect(spyOnHide).toHaveBeenCalled();
      });
    });
  });
});

@Component({
  selector: 'app-fake-risk-assessment-component',
  template: '',
})
class FakeRiskAssessmentComponent {}
